"""
This is the class to read the image or pdf files and return the ocr text results.
The image could be image with cropped region data.
"""

from FuncMl import FuncMl
from extractors import CurrencyExtractor
from extractors import DateExtractor
from extractors import StringExtractor
from field_hints import Coordinates
from field_hints import Proximity
from fuzzywuzzy import fuzz
import numpy as np
import cv2


def get_coordinates_hint(hint):
    for sub_hint in hint:
        if sub_hint[0] == 'coordinates':
            return sub_hint[1]


def get_proximity_hint(hint):
    ret = []
    for sub_hint in hint:
        if sub_hint[0] == 'proximity':
            ret.append(sub_hint[1])

    return ret


def get_page(hint_hash):
    if 'page' in hint_hash:
        return hint_hash['page']
    else:
        return 1


def get_field_id(hint_hash):
    if 'field_id' in hint_hash:
        return hint_hash['field_id']
    else:
        return None


def get_accepted_chars(hint):
    for sub_hint in hint:
        if sub_hint[0] == 'accepted_chars':
            return sub_hint[1]


def get_accepted_lengths(hint):
    for sub_hint in hint:
        if sub_hint[0] == 'accepted_lengths':
            return sub_hint[1]


def get_size(profile_hint):
    if profile_hint is None:
        m_w = 8.5
        m_h = 11.0
    else:
        m_w = profile_hint['width']
        m_h = profile_hint['height']

    return m_w, m_h


def get_match_distance(hint_data, match_pos):

    dist_match = []

    for i in range(len(match_pos)):
        match_center_x = int((match_pos[i][0] + match_pos[i][2]) / 2)
        match_center_y = int((match_pos[i][1] + match_pos[i][3]) / 2)

        dist_list = []
        for k1 in range(len(hint_data)):
            for k2 in range(len(hint_data[k1])):
                proximity_hint = hint_data[k1][k2][0]
                hint_pos = hint_data[k1][k2][1]
                hint_center_x = int((hint_pos[0] + hint_pos[2]) / 2)
                hint_center_y = int((hint_pos[1] + hint_pos[3]) / 2)

                if proximity_hint == 'same_line_prefix':
                    dist = abs(hint_center_y - match_center_y) * 10 + abs(match_pos[i][0] - hint_pos[2])
                elif proximity_hint == 'above_text':
                    dist = abs(hint_center_x - match_center_x) + abs(match_pos[i][1] - hint_pos[3]) * 10
                elif proximity_hint == 'same_line_suffix':
                    dist = abs(hint_center_y - match_center_y) * 10 + abs(hint_pos[0] - match_pos[i][2])
                else:
                    dist = abs(hint_center_x - match_center_x) + abs(hint_pos[1] - match_pos[i][3]) * 10

                dist_list.append(dist)

        dist_match.append(min(dist_list))

    return dist_match


def date_convert(text):
    month_list = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    month_list_full = ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september',
                       'october', 'november', 'december']

    if month_list_full.__contains__(text.lower()):
        return str(month_list_full.index(text.lower()) + 1)
    elif month_list.__contains__(text.lower()):
        return str(month_list.index(text.lower()) + 1)
    else:
        return text


class FieldExtractor:
    def __init__(self):
        """
            class initial function
        """
        self.class_func = FuncMl()
        self.currency_extractor = CurrencyExtractor()
        self.date_extractor = DateExtractor()
        self.string_extractor = StringExtractor()
        self.hint_coordinates = Coordinates()
        self.hint_proximity = Proximity()
        self.sleep_time = 0.5
        self.dict_list = []

    def find_match(self, text, match_type, hint_hash, proximity_hint, country='US'):
        proximity_text = []
        for i in range(len(proximity_hint)):
            if 'text' in proximity_hint[i]:
                proximity_text.append(proximity_hint[i]['text'])

        if match_type == 'date':
            result_value = self.date_extractor.extract(text, country=country)
        elif match_type == 'currency':
            result_value = self.currency_extractor.extract(text)
        elif match_type == 'string':
            accepted_chars = get_accepted_chars(hint_hash)
            accepted_len = get_accepted_lengths(hint_hash)
            result_value = self.string_extractor.extract(text, accepted_chars, accepted_len, proximity_text)
        else:
            result_value = []

        # check if result_value is part of proximity hint key
        result = []
        for i in range(len(result_value)):
            f_key = False
            for j in range(len(proximity_text)):
                if proximity_text[j].__contains__(result_value[i]):
                    f_key = True
                    break

            if not f_key:
                result.append(result_value[i])

        return result

    def extract_v2(self, filename, profile, hints, ocr_json_data=None, en_fuzzy=True, country='US', select_first=False):

        if type(hints) == dict:
            hints = [hints]

        dict_list = []
        ocr_json_list = {}

        # ------------------------- get ocr json of pages --------------------
        if ocr_json_data is None:
            img_list, temp_list, json_list = self.class_func.get_img_list(filename)

            for ind in range(len(hints)):
                page = get_page(hints[ind])
                if page not in ocr_json_list:
                    if json_list and json_list[page - 1] is not None:
                        ocr_json_list[page] = json_list[page - 1]
                    else:
                        ocr_json_list[page] = self.class_func.get_json_google_from_jpg(img_list[page - 1])

        else:
            img_list = [filename]
            temp_list = []
            ocr_json_list[1] = ocr_json_data

        for ind in range(len(hints)):
            # -------- get the hint_hash data and convert to 'date' if field is 'date_terms' ------
            hint_hash = hints[ind]
            page = get_page(hint_hash)
            ocr_json = self.change_json(ocr_json_list[page])

            if hint_hash['data_type'] == 'date_terms':
                hint_hash['data_type'] = 'date'
                del hint_hash['value']

            # ------------------- calling of field extract function using hint_hash -----------------
            f_dict = self.__extract_hash(img_list[page-1], ocr_json, profile, hint_hash,
                                         en_fuz=en_fuzzy, country=country, sel_first=select_first)
            if f_dict is not None:
                dict_list.append(f_dict)

        for i in range(len(temp_list)):
            self.class_func.rm_file(temp_list[i])

        return sorted(dict_list, key=lambda k: k['field_id'])

    def __extract_hash(self, img_page, page_json, profile_hash, hint_hash, en_fuz=True, country='US', sel_first=False):
        f_dict = {'field_id': get_field_id(hint_hash), 'field_name': hint_hash['name'], 'value': None}

        if 'hints' in hint_hash:
            # ---------- Get the matching text and it's count using coordinates hint ------------
            m_width, m_height = get_size(profile_hash)
            match_type = hint_hash['data_type']

            img = cv2.imread(img_page)

            for hint_ind in range(len(hint_hash['hints'])):
                hint = hint_hash['hints'][hint_ind]
                proximity_hint = get_proximity_hint(hint)
                coordinate_hint = get_coordinates_hint(hint)

                ocr_json = self.hint_coordinates.get_data(page_json, img_page, coordinate_hint, m_width, m_height)

                result_value = None

                if ocr_json is not None and img is not None:
                    img_h, img_w, _ = np.shape(img)
                    rate_x = float(img_w) / m_width
                    rate_y = float(img_h) / m_height

                    for i in range(1, len(ocr_json)):
                        p = ocr_json[i]['boundingPoly']['vertices']
                        cv2.rectangle(img, (self.class_func.dict_int(p[0], 'x'), self.class_func.dict_int(p[0], 'y')),
                                      (self.class_func.dict_int(p[1], 'x'), self.class_func.dict_int(p[2], 'y')),
                                      (0, 0, 255), 1)

                    if len(proximity_hint) == 0:
                        ocr_str = ocr_json[0]['description']
                        match_result = self.find_match(ocr_str, match_type, hint, proximity_hint, country)

                        if len(self.class_func.remove_duplicate(match_result)) == 1:
                            result_value = match_result[0]
                        elif len(self.class_func.remove_duplicate(match_result)) > 1 and sel_first:
                            result_value = match_result[0]
                        else:
                            result_value = None

                    else:
                        # ---------- Get the matching text and it's count using proximity hint ------------
                        new_text, hint_pos, text_list, text_pos = \
                            self.hint_proximity.get_data(ocr_json, proximity_hint, match_type,
                                                         rate_x, rate_y, en_fuzzy=en_fuz)
                        match_result_new = self.find_match(new_text, match_type, hint, proximity_hint, country)

                        for i in range(len(hint_pos)):
                            for j in range(len(hint_pos[i])):
                                cv2.rectangle(img, (hint_pos[i][j][1][0], hint_pos[i][j][1][1]),
                                              (hint_pos[i][j][1][2], hint_pos[i][j][1][3]), (255, 0, 0), 2)
                        for i in range(len(text_pos)):
                            cv2.rectangle(img, (text_pos[i][0], text_pos[i][1]),
                                          (text_pos[i][2], text_pos[i][3]), (0, 255, 0), 1)

                        match_result_new = self.class_func.remove_duplicate(match_result_new)
                        if len(match_result_new) == 0:
                            result_value = None
                        elif len(match_result_new) == 1:
                            result_value = match_result_new[0]
                        else:
                            pro_list = []
                            for i in range(len(proximity_hint)):
                                pro_list.append(proximity_hint[i]['type'])

                            pro_list = self.class_func.remove_duplicate(pro_list)

                            if len(pro_list) == 1:  # all proximity have same type
                                match_pos = self.get_match_pos(match_result_new, text_list, text_pos, match_type, hint,
                                                               proximity_hint)
                                match_distance = get_match_distance(hint_pos, match_pos)
                                result_value = match_result_new[np.argmin(match_distance)]
                            else:
                                result_value = None

                    cv2.imwrite('a_rect.jpg', img)

                f_dict['value'] = result_value

                if match_type == 'currency':
                    if result_value is not None and float(result_value) > 0:
                        break
                elif result_value is not None:
                    break

        elif 'value' in hint_hash:
            # -------------------- get the 'value' data if has 'value' field --------------------
            f_dict['value'] = hint_hash['value']

        else:
            f_dict = None

        return f_dict

    def get_match_pos(self, match_result_new, text_list, text_pos, match_type, hint, proximity_hint):

        match_pos = []

        for i in range(len(match_result_new)):
            match_score_max = 0
            opt_word_cnt = 0
            opt_start_pos = 0

            for word_cnt in range(5):
                for j in range(len(text_list) - word_cnt):
                    str_combine1 = text_list[j]
                    str_combine2 = text_list[j]
                    for k in range(word_cnt):
                        str_combine1 += text_list[j + k + 1]
                        str_combine2 += (' ' + text_list[j + k + 1])

                    if match_result_new[i].count('/') == 2:    # when date
                        str_combine3 = date_convert(text_list[j])
                        str_combine4 = date_convert(text_list[j])
                        for k in range(word_cnt):
                            str_combine3 += date_convert(text_list[j + k + 1])
                            str_combine4 += (' ' + date_convert(text_list[j + k + 1]))
                    else:
                        str_combine3 = ''
                        str_combine4 = ''

                    ret_conv1 = self.find_match(str_combine1, match_type, hint, proximity_hint)
                    ret_conv2 = self.find_match(str_combine2, match_type, hint, proximity_hint)
                    match_score1 = fuzz.ratio(match_result_new[i], str_combine1)
                    match_score2 = fuzz.ratio(match_result_new[i], ret_conv1)
                    match_score3 = fuzz.ratio(match_result_new[i], ret_conv2)

                    match_score = max(match_score1, match_score2, match_score3)

                    if match_result_new[i].count('/') == 2:
                        ret_conv3 = self.find_match(str_combine3, match_type, hint, proximity_hint)
                        ret_conv4 = self.find_match(str_combine4, match_type, hint, proximity_hint)
                        match_score4 = fuzz.ratio(match_result_new[i], str_combine3)
                        match_score5 = fuzz.ratio(match_result_new[i], ret_conv3)
                        match_score6 = fuzz.ratio(match_result_new[i], ret_conv4)

                        match_score = max(match_score, match_score4, match_score5, match_score6)

                    if match_score > match_score_max:
                        match_score_max = match_score
                        opt_word_cnt = word_cnt
                        opt_start_pos = j

            if not text_pos:
                break

            match_score_max_pos = text_pos[opt_start_pos]

            for k in range(opt_word_cnt):
                match_score_max_pos = [min(match_score_max_pos[0], text_pos[opt_start_pos + k + 1][0]),
                                       min(match_score_max_pos[1], text_pos[opt_start_pos + k + 1][1]),
                                       max(match_score_max_pos[2], text_pos[opt_start_pos + k + 1][2]),
                                       max(match_score_max_pos[3], text_pos[opt_start_pos + k + 1][3])]

            for k in range(opt_word_cnt + 1):
                text_list.pop(opt_start_pos)
                text_pos.pop(opt_start_pos)

            match_pos.append(match_score_max_pos)

        return match_pos

    def change_json(self, page_json):
        """
            Change "No Payment Due" -> "0"
        """
        if page_json is None:
            return None

        for i in range(1, len(page_json) - 2):
            text1 = page_json[i]['description']
            text2 = page_json[i + 1]['description']
            text3 = page_json[i + 2]['description']
            rect1 = self.class_func.get_rect_ocr_data(page_json, i)
            rect2 = self.class_func.get_rect_ocr_data(page_json, i + 1)
            rect3 = self.class_func.get_rect_ocr_data(page_json, i + 2)

            if text1 == 'No' and text2 == 'Payment' and text3 == 'Due':
                if self.class_func.check_same_line(rect1, rect2) and self.class_func.check_same_line(rect2, rect3):
                    page_json[i + 1]['description'] = '0.0'

        return page_json
