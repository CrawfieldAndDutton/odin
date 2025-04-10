import re
from bs4 import BeautifulSoup


class GSTINScraper:
    @staticmethod
    def extract_gst_data(response, gstin_request):
        soup = BeautifulSoup(response.text, "html.parser")

        result = {
            "status": "success" if response.status_code == 200 else "failure",
            "status_code": response.status_code,
            "message": "GSTIN FOUND" if response.status_code == 200 else "GSTIN NOT FOUND",
        }

        if response.status_code != 200:
            return result

        result.update({
            "gstin": GSTINScraper._extract_gstin(soup, gstin_request),
            "gstin_details": GSTINScraper._extract_gstin_details(soup),
            "hsn/sac": GSTINScraper._extract_hsn_sac(soup),
            "business_owners": GSTINScraper._extract_business_owners(soup),
            "other_gstin": GSTINScraper._extract_other_gstin(soup),
            "fillingFreq": GSTINScraper._extract_filling_frequency(soup),
            "returns": GSTINScraper._extract_returns(soup)
        })

        return result

    @staticmethod
    def _extract_gstin(soup, gstin_request):
        title = soup.find('title')
        if not title:
            return gstin_request

        title_text = title.get_text()
        gstin_match = re.search(r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', title_text)
        return gstin_match.group() if gstin_match else gstin_request

    @staticmethod
    def _extract_gstin_details(soup):
        details = {}
        details_heading_div = soup.find("div", string=lambda text: text and "Details" in text)
        if not details_heading_div:
            return details

        section = details_heading_div.find_parent("section")
        for info_div in section.select("div.flex.flex-col > div"):
            label_tag = info_div.find("p", class_="text-cyan-700")
            if not label_tag or "Aggregate Turnover" in label_tag.get_text(strip=True):
                continue

            label = label_tag.get_text(strip=True)
            label = label.lower().replace(" ", "_").replace("?", "").replace("_(address)", "").replace("e-i", "e_i")
            if info_div.find_all("span"):
                value = " ".join(span.get_text(strip=True) for span in info_div.find_all("span"))
            else:
                next_elem = label_tag.find_next_sibling(["h2", "p"])
                value = next_elem.get_text(strip=True) if next_elem else "N/A"

            details[label] = value

        return details

    @staticmethod
    def _extract_hsn_sac(soup):
        hsn_codes = []
        hsn_div = soup.find("div", string=lambda text: text and "HSN / SAC" in text)
        if not hsn_div:
            return hsn_codes

        hsn_section = hsn_div.find_parent("section")
        hsn_items = hsn_section.find_all("li", class_="text-xl") if hsn_section else []
        return [item.get_text(strip=True) for item in hsn_items if item.get_text(strip=True)]

    @staticmethod
    def _extract_business_owners(soup):
        owners = []
        business_div = soup.find("div", string=lambda text: text and "Business Owners" in text)
        if not business_div:
            return owners

        business_section = business_div.find_parent("section")
        owner_divs = business_section.find_all("h2") if business_section else []
        return [div.get_text(strip=True) for div in owner_divs if div.get_text(strip=True)]

    @staticmethod
    def _extract_other_gstin(soup):
        other_gstins = []
        heading_div = soup.find("div", string=lambda text: text and "Other GSTIN of the PAN" in text)
        if not heading_div:
            return other_gstins

        section = heading_div.find_parent("section")
        li_tags = section.select("ul li") if section else []
        for li in li_tags:
            a = li.find("a")
            if a and a.find("span"):
                gstin = a.contents[0].strip()
                state_code = a.find("span").text.strip()
                other_gstins.append(f"{gstin} {state_code}")

        return other_gstins

    @staticmethod
    def _extract_filling_frequency(soup):
        freq_data = []
        freq_header = soup.find('div', string=lambda text: text and 'Return Periodicity' in text)
        if not freq_header:
            return freq_data

        freq_section = freq_header.find_parent('section')
        freq_items = freq_section.find_all('div', class_='grid') if freq_section else []
        if freq_items:
            freq_divs = freq_items[0].find_all('div')
            freq_data = [div.get_text(strip=True).replace('M', ' M') for div in freq_divs]

        return freq_data

    @staticmethod
    def _extract_returns(soup):
        returns = []
        for table in soup.find_all('table', class_='border'):
            caption = table.find('caption')
            if not caption:
                continue

            return_type = caption.get_text(strip=True)
            for row in table.find('tbody').find_all('tr'):
                cells = row.find_all('td')
                if len(cells) != 3:
                    continue

                returns.append({
                    "fy": cells[0].get_text(strip=True),
                    "filling_date": cells[2].get_text(strip=True),
                    "return_type": return_type,
                    "period": cells[1].get_text(strip=True)
                })

        return returns
