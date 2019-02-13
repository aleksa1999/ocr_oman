
from Categorization import FuncMl
from extractors import CurrencyExtractor
from extractors import DateExtractor


class TextExtractor:

    def __init__(self, country='US'):
        self.class_func = FuncMl()
        self.currency_extractor = CurrencyExtractor()
        self.date_extractor = DateExtractor()
        self.country = country

    def find_match_text(self, text, match_type, key_sub_type='', country='US'):
        result_value = []
        if match_type == 'date':
            result_value = self.date_extractor.extract(text, country=country)
        elif match_type == 'currency':
            if len(text.split()) < 3:
                result_value = self.currency_extractor.extract(text)
        elif match_type == 'string':
            f_digit = False
            f_string = False
            f_upper = True

            # if len(text) > 30:
            #     text = text.split()[0]

            for i in range(len(text)):
                if text[i].isdigit():
                    f_digit = True
                elif text[i].isalpha():
                    f_string = True
                    if not text[i].isupper():
                        f_upper = False
                        break

            if key_sub_type == 'phone':
                if not f_string and f_digit:
                    result_value = [text]
            elif key_sub_type == 'email':
                if f_string and '@' in text and '.' in text:
                    result_value = [text]
            elif key_sub_type == 'url':
                if (text.startswith('www') or text.startswith('http')) and '.' in text:
                    result_value = [text]
            elif key_sub_type == 'alphabet':
                if text.isalpha():
                    result_value = [text]
            elif key_sub_type == 'upper':
                if text.isupper():
                    result_value = [text]
            elif key_sub_type == 'digit':
                if text.isdigit():
                    result_value = [text]
            elif key_sub_type == 'no_digit':
                if not f_digit:
                    result_value = [text]
            else:
                if f_upper and f_digit and len(text) >= 3:
                    result_value = [text]

        return result_value

    def extract_v1(self, ocr_text_lines, ocr_rect_lines, key_type, key_list, key_sub_type):
        """
            :param ocr_text_lines: list of text lines from ocr_json
            :param ocr_rect_lines: list of rect lines from ocr_json
            :param key_type: "date"
            :param key_list: ["Invoice Date", "Date"]
            :return: result
        """
        raw_text = ''
        for sub_key in key_list:
            for i in range(1, len(ocr_text_lines)):
                if sub_key.startswith('Head ') and ocr_text_lines[i].startswith(sub_key):
                    if ocr_text_lines[i + 7].count('/') == 2 and ocr_text_lines[i + 6].startswith("Registration"):
                        raw_text = ocr_text_lines[i + 7]
                    elif ocr_text_lines[i + 12].count('/') == 2 and ocr_text_lines[i + 10] == 'Active':
                        raw_text = ocr_text_lines[i + 12]
                    elif ocr_text_lines[i + 11].count('/') == 2 and ocr_text_lines[i + 7] == 'Active' and ocr_text_lines[i + 10] == 'Fiscal Year End:':
                        raw_text = ocr_text_lines[i + 11]

                elif sub_key == ocr_text_lines[i] == "Commercial Name":
                    if ocr_text_lines[i + 3] == "Legal Type":
                        raw_text = ocr_text_lines[i + 2]
                    elif ocr_text_lines[i + 5] == "Legal Type":
                        raw_text = ocr_text_lines[i + 4]
                    elif ocr_text_lines[i + 9] == "Legal Type" and ocr_text_lines[i + 1].isdigit():
                        raw_text = ocr_text_lines[i + 4]

                elif sub_key == 'Surname' and ocr_text_lines[i].__contains__('Surname'):
                    if ocr_text_lines[i+1].__contains__('Title') and ocr_text_lines[i+4].__contains__('Given Names'):
                        raw_text = ocr_text_lines[i + 2]
                        key_sub_type = 'no_digit'
                    elif ocr_text_lines[i+2].__contains__('Title') and ocr_text_lines[i+4].__contains__('Given Names'):
                        raw_text = ocr_text_lines[i + 1]
                        key_sub_type = 'no_digit'
                    elif ocr_text_lines[i + 3].__contains__('Given'):
                        raw_text = ocr_text_lines[i + 1]
                        key_sub_type = 'no_digit'

                elif sub_key == 'Given Names' and ocr_text_lines[i].__contains__('Given'):
                    if ocr_text_lines[i + 3] == 'Nationality':
                        raw_text = ocr_text_lines[i + 1]
                        key_sub_type = 'no_digit'
                    elif ocr_text_lines[i + 4].__contains__('Nationality'):
                        raw_text = ocr_text_lines[i + 2] + ' ' + ocr_text_lines[i + 1]
                        key_sub_type = 'no_digit'
                    elif ocr_text_lines[i + 5].__contains__('Nationality'):
                        raw_text = ocr_text_lines[i + 1]
                        key_sub_type = 'no_digit'
                    elif ocr_text_lines[i + 7].__contains__('Nationality') and ocr_text_lines[i + 3].__contains__('ID'):
                        raw_text = ocr_text_lines[i + 1]
                        key_sub_type = 'no_digit'

                if raw_text != '':
                    result = self.find_match_text(raw_text.strip(), key_type, key_sub_type, self.country)
                    if result:
                        return result[0]

                if sub_key == ocr_text_lines[i]:
                    if i < len(ocr_text_lines):
                        if ocr_rect_lines[i][1] > ocr_rect_lines[i + 1][1] + 10:
                            continue
                        else:
                            raw_text = ocr_text_lines[i + 1]

                elif ocr_text_lines[i].startswith(sub_key + ':'):
                    if len(ocr_text_lines[i]) == len(sub_key) + 1:
                        raw_text = ocr_text_lines[i + 1]
                    else:
                        raw_text = ocr_text_lines[i][len(sub_key) + 1:]

                elif ocr_text_lines[i].startswith(sub_key + ' :'):
                    if len(ocr_text_lines[i]) == len(sub_key) + 2:
                        raw_text = ocr_text_lines[i + 1]
                    else:
                        raw_text = ocr_text_lines[i][len(sub_key) + 2:]

                elif ocr_text_lines[i].startswith(sub_key):
                    raw_text = ocr_text_lines[i][len(sub_key):]

                else:
                    continue

                result = self.find_match_text(raw_text.strip(), key_type, key_sub_type, self.country)

                if result:
                    return result[0]

        return None
