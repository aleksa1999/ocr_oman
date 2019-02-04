
from Categorization import FieldExtractor
from Categorization import FuncMl


class ReceiptAmountExtractor:

    def __init__(self):
        self.class_field_extractor = FieldExtractor()
        self.class_func = FuncMl()

        self.amount_key_list, self.amount_no_key_list = self.class_func.load_receipt_amt_keys()

    def extract_receipt_amount_keys(self, filename, ocr_json=None):
        # ---------------------------- Get OCR json -------------------------------
        if ocr_json is None:
            ocr_json = self.class_func.get_json_google_from_jpg(filename)

        if ocr_json is None:
            return [], []

        detect_keys = []
        key_words = 0

        for i in range(1, len(ocr_json) - 2):
            if ocr_json[i]['description'] == '' or ocr_json[i]['description'][0].islower():
                continue

            # ------------- Get Candidate of amount keys and it's position ------------
            text1 = ocr_json[i]['description'].lower()
            text2 = text1 + ' ' + ocr_json[i + 1]['description'].lower()
            text3 = text2 + ' ' + ocr_json[i + 2]['description'].lower()
            text_pos1 = self.class_func.get_rect_ocr_data(ocr_json, i)
            text_pos2 = self.class_func.get_rect_ocr_data(ocr_json, i + 1)
            text_pos3 = self.class_func.get_rect_ocr_data(ocr_json, i + 2)

            if key_words > 1:
                key_words -= 1
                continue

            if text2 in self.amount_no_key_list:
                key_words = 2
                continue
            elif text3 in self.amount_no_key_list:
                key_words = 3
                continue

            if text3 in self.amount_key_list and self.class_func.check_same_line(text_pos1, text_pos2) and \
                    self.class_func.check_same_line(text_pos2, text_pos3):
                amount_key = text3
                key_words = 3
            elif text2 in self.amount_key_list and self.class_func.check_same_line(text_pos1, text_pos2):
                amount_key = text2
                key_words = 2
            elif text1 in self.amount_key_list:
                amount_key = text1
                key_words = 1
            else:
                continue

            # ------------------------ Get value of candidates ------------------------
            profile_hash = {u'width': 8.5, u'height': 11}
            key_y1 = text_pos1[1] - 200
            key_y2 = text_pos1[3] + 200
            hint_hash = {u'field_id': 2, u'data_type': u'currency',
                         u'hints': [[
                             [u'coordinates', {u'x_1': 0.0, u'x_2': 8.5, u'y_1': key_y1, u'y_2': key_y2}],
                             [u'proximity', {u'text': amount_key, u'type': u'same_line_prefix'}]
                         ]]}

            ret_val = self.class_field_extractor.extract_v2(filename, profile_hash, hint_hash, ocr_json_data=ocr_json)
            amount_value = ret_val[0]['value']

            if amount_value is None:
                continue
            elif amount_value == 0 and amount_key == 'total':
                continue

            # ------------- Get number of words on left and right of value ------------
            key_x1 = text_pos1[0]
            if key_words == 3:
                key_x2 = text_pos3[2]
            elif key_words == 2:
                key_x2 = text_pos2[2]
            else:
                key_x2 = text_pos1[2]

            # ----- find all same line words ------
            center_line = int((text_pos1[1] + text_pos1[3]) / 2)

            line_word_text = []
            line_word_pos = []

            for j in range(1, len(ocr_json) - 2):
                word_pos = self.class_func.get_rect_ocr_data(ocr_json, j)

                if word_pos[1] < center_line < word_pos[3]:
                    word_text = ocr_json[j]['description'].lower()
                    line_word_text.append(word_text)
                    line_word_pos.append(word_pos)

            # ----- get x position of value word -----
            value_x1 = 0
            value_x2 = 0

            for j in range(len(line_word_text)):
                if line_word_pos[j][0] < key_x2:
                    continue

                if line_word_text[j].isdigit() and int(line_word_text[j]) == int(amount_value):
                    value_x1 = line_word_pos[j][0]
                    value_x2 = line_word_pos[j][2]

                    if j < len(line_word_pos) - 2 and line_word_text[j + 2].isdigit() and \
                            (line_word_text[j + 1] == '.' or line_word_text[j + 1] == ',') and \
                            float(line_word_text[j] + '.' + line_word_text[j + 2]) == float(amount_value):
                        value_x2 = line_word_pos[j + 2][2]
                        break

            # ----- count the words -----
            cnt1 = 0
            cnt2 = 0
            cnt3 = 0
            for j in range(len(line_word_text)):
                if not (line_word_text[j].isdigit() or line_word_text[j].isalpha()):
                    continue
                if line_word_pos[j][2] < key_x1:
                    cnt1 += 1
                elif key_x2 < line_word_pos[j][0] < value_x1:
                    cnt2 += 1
                elif value_x2 < line_word_pos[j][0]:
                    cnt3 += 1

            detect_keys.append([amount_key, amount_value, text_pos1, [cnt1, cnt2, cnt3], [0, 0, 0, 0]])

        # ----------------------- Get relative position of keys -----------------------
        for i in range(len(detect_keys) - 1):
            if self.class_func.check_same_line(detect_keys[i][2], detect_keys[i + 1][2]):
                detect_keys[i][4][0] = i + 2
                detect_keys[i + 1][4][1] = i + 1
            else:
                detect_keys[i][4][2] = i + 2
                detect_keys[i + 1][4][3] = i + 1

        # ------------------------ Create key-value dictionary ------------------------
        dict_val = {}
        dict_temp = {}

        for i in range(len(detect_keys)):
            key_name = detect_keys[i][0]

            if key_name in dict_val:
                if dict_temp[key_name] > sum(detect_keys[i][3]):
                    dict_val[key_name] = detect_keys[i][1]
                    dict_temp[key_name] = sum(detect_keys[i][3])
            else:
                dict_val[key_name] = detect_keys[i][1]
                dict_temp[key_name] = sum(detect_keys[i][3])

        # ---------------------------- Create feature list ----------------------------
        feature_list = []

        for i in range(len(detect_keys)):
            feature_list.append([detect_keys[i][0], detect_keys[i][3], detect_keys[i][4]])

        return dict_val, feature_list

    def extract(self, filename, ocr_json=None):

        key_val_list, key_data = self.extract_receipt_amount_keys(filename, ocr_json)

        if not key_data:
            return None

        for amount_key in self.amount_key_list:
            if amount_key in key_val_list:
                return key_val_list[amount_key]

        return None
