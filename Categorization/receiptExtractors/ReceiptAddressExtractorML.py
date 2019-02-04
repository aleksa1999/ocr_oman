
from Categorization import FuncMl
import os


class ReceiptAddressExtractorML:

    def __init__(self):
        self.class_func = FuncMl()

        self.list_state_abbr = self.get_state_abbreviation_us()

        self.x_list = []
        self.y_list = []

    def get_state_abbreviation_us(self):
        us_postal_data = self.class_func.load_csv(os.path.join(self.class_func.my_dir, 'config/us_postal_codes.csv'))
        list_state_abbr = []
        for i in range(1, len(us_postal_data)):
            list_state_abbr.append(us_postal_data[i][3].lower())

        list_state_abbr.append('california')

        return self.class_func.remove_duplicate(list_state_abbr)

    def __mark_address_line(self, text_lines):
        """
            Check and mark the address lines
        """
        mark_list = []
        key_address = ['street', 'road', 'rd', 'ave', 'st', 'way', 'city', 'dr', 'ste', 'floor', 'station', 'airport',
                       'mall', 'center', 'blvd', 'expressway']
        no_key_list = [':', '%', ' ID.', '.com', 'Visa ending']

        # for i in range(min(len(text_lines), 10)):
        for i in range(1, len(text_lines)):
            text_line = text_lines[i].lower()
            word_line = text_line.replace(',', ' ').split()
            f_digit = False
            f_key1 = False
            f_key2 = False

            # Check no_key
            f_no = False
            for no_key in no_key_list:
                if text_lines[i].__contains__(no_key):
                    f_no = True
                    break

            if f_no:
                continue

            # Check address keys
            for j in range(len(word_line)):
                if word_line[j].replace('-', '').isdigit():
                    f_digit = True

                if key_address.__contains__(word_line[j].strip('.').strip(',')):
                    f_key1 = True

                if self.list_state_abbr.__contains__(word_line[j].strip('.').strip(',')):
                    f_key2 = True

            if f_key1:  # `First Street White Luncheon Napkins 1500 ch`
                for j in range(len(word_line)):
                    if word_line[j].isdigit():
                        break
                    if j >= 4:
                        f_key1 = False

            if not f_key2:
                for k in range(len(self.list_state_abbr)):
                    if len(self.list_state_abbr[k].split()) > 1:
                        if text_line.__contains__(self.list_state_abbr[k].lower()):
                            f_key2 = True

            if f_key1:
                mark_list.append(i)
            elif f_key2:
                if f_digit:
                    mark_list.append(i)
                elif i + 1 < len(text_lines) and text_lines[i + 1].isdigit() and 3 < len(text_lines[i + 1]) < 6:
                    mark_list.append(i)
                    mark_list.append(i + 1)

        # check previous line if address is 1 line:  '1298 Montague Expw \nSan Jose CA 95131'
        if len(mark_list) == 1:
            if mark_list[0] > 0:
                temp_line = text_lines[mark_list[0] - 1]
                temp_word = temp_line.split()
                if temp_word[0].isdigit() and len(temp_word) >= 3:
                    mark_list.insert(0, mark_list[0] - 1)

        return mark_list

    def __detect_line_item_section(self, ocr_json):
        # ------------------- Get rect of individual words --------------------
        rects = []
        total_height = 0
        for i in range(1, len(ocr_json)):
            word_rect = self.class_func.get_rect_ocr_data(ocr_json, i)
            total_height += (word_rect[3] - word_rect[1])
            rects.append(word_rect)

        # ------------------- Merge rects of top/bottom words -----------------
        char_h = int(total_height / len(ocr_json) / 2)

        while True:
            f_merge = False
            for i in range(len(rects) - 20):
                for j in range(i + 1, i + 20):
                    if abs(rects[i][0] - rects[j][0]) < char_h and abs(rects[i][2] - rects[j][2]) < char_h and \
                            (abs(rects[i][1] - rects[j][3]) < char_h or abs(rects[i][3] - rects[j][1]) < char_h):
                        rects[i] = self.class_func.merge_rect(rects[i], rects[j])
                        rects.pop(j)
                        f_merge = True
                        break

                if f_merge:
                    break

            if not f_merge:
                break

        # ------------------- Detect the long height rects --------------------
        long_rect = []
        for i in range(len(rects)):
            if rects[i][3] - rects[i][1] > char_h * 10:
                long_rect.append(rects[i])

        if len(long_rect) > 2:
            for i in range(len(long_rect)):
                same_line_cnt = 0
                for j in range(len(long_rect)):
                    if abs(long_rect[i][1] - long_rect[j][1]) < char_h:
                        same_line_cnt += 1

                if same_line_cnt > 2:
                    line_data = self.class_func.get_line_rect(ocr_json)

                    for j in range(len(line_data['rect'])):
                        if line_data['rect'][j][1] >= long_rect[i][3]:
                            return j - 1

            return -1

        else:
            return -1

    def get_features_address(self, ocr_json):

        new_ocr_text = self.class_func.remove_vertical_text(ocr_json)
        text_lines = new_ocr_text.splitlines()

        address_line_list = self.__mark_address_line(text_lines)
        mark_address_list = []

        if address_line_list:
            mark_start = address_line_list[0]
            mark_len = 1
            text_address = text_lines[address_line_list[0]]

            for i in range(1, len(address_line_list)):
                if address_line_list[i] == address_line_list[i - 1] + 1:
                    mark_len += 1
                    text_address += ' ' + text_lines[address_line_list[i]]
                else:
                    mark_address_list.append([mark_start, mark_len, text_address])
                    mark_start = address_line_list[i]
                    mark_len = 1
                    text_address = text_lines[address_line_list[i]]

            if 10 < len(text_address) < 60:
                mark_address_list.append([mark_start, mark_len, text_address])

        return mark_address_list

    def extractor(self, ocr_json):

        mark_address_list = self.get_features_address(ocr_json)
        first_address_line = -1

        if mark_address_list:
            first_address_line = mark_address_list[0][0]
            ret_address = mark_address_list[0][2]

        else:
            ret_address = ''

        return ret_address, first_address_line
