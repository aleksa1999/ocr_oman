
from Categorization import FuncMl
from Categorization import constant
import itertools
from fuzzywuzzy import fuzz


class Proximity:

    def __init__(self):
        """
            class initial function
        """
        self.class_func = FuncMl()

    def get_position(self, dst_word, ocr_json, data_type, en_fuzzy=True):

        pos_list = []
        pos_list_temp = []

        if dst_word[0] == '(':
            dst_word = '( ' + dst_word[1:]

        if dst_word[-1] == ':':
            dst_word = dst_word[:-1] + ' :'
        elif dst_word[-1] == ')':
            dst_word = dst_word[:-1] + ' )'
        elif dst_word[-1] == '#':
            dst_word = dst_word[:-1] + ' #'
        elif dst_word[-1] == '.':
            dst_word = dst_word[:-1]

        dst_word_list = dst_word.split()

        # ---------------- check strict AND logic of dst words ------------------
        for i in range(1, len(ocr_json)-len(dst_word_list)+1):
            if i < len(ocr_json) - 1:
                comb_text = ocr_json[i]['description'].lower() + ' ' + ocr_json[i + 1]['description'].lower()
                if constant.no_hint_list.__contains__(comb_text):
                    continue

            f_match = True
            for j in range(len(dst_word_list)):
                if not ocr_json[i+j]['description'].lower() == dst_word_list[j].lower():
                    f_match = False
                    break

            if f_match:
                rect = self.get_rect(ocr_json[i]['boundingPoly']['vertices'])

                for j in range(1, len(dst_word_list)):
                    rect_next = self.get_rect(ocr_json[i+j]['boundingPoly']['vertices'])
                    rect = self.class_func.merge_rect(rect, rect_next)

                # check existence of next word
                rect_last = self.get_rect(ocr_json[i + len(dst_word_list) - 1]['boundingPoly']['vertices'])

                if len(ocr_json) > i + len(dst_word_list):
                    rect_last_next = self.get_rect(ocr_json[i + len(dst_word_list)]['boundingPoly']['vertices'])
                    word_last_next = ocr_json[i + len(dst_word_list)]['description']

                    if abs(rect_last_next[0] - rect_last[2]) < (rect[2] - rect[0]) / len(dst_word) * 2 and \
                            abs(rect_last_next[1] - rect_last[1]) < 10 and \
                            data_type == 'currency' and word_last_next.isalpha():
                        pos_list_temp.append(rect)
                    else:
                        pos_list.append(rect)

                else:
                    pos_list.append(rect)

        if not pos_list and pos_list_temp:
            pos_list = pos_list_temp

        # ---------------- check smooth AND logic of dst words ------------------
        if not pos_list:
            for i in range(1, len(ocr_json)-len(dst_word_list)):
                comb_text = ocr_json[i]['description'].lower() + ' ' + ocr_json[i + 1]['description'].lower()
                if constant.no_hint_list.__contains__(comb_text):
                    continue

                f_match = True
                for j in range(len(dst_word_list)):
                    if not ocr_json[i+j]['description'].lower().__contains__(dst_word_list[j].lower()):
                        f_match = False
                        break

                if f_match:
                    rect = self.get_rect(ocr_json[i]['boundingPoly']['vertices'])

                    for j in range(1, len(dst_word_list)):
                        rect_next = self.get_rect(ocr_json[i+j]['boundingPoly']['vertices'])
                        rect = self.class_func.merge_rect(rect, rect_next)

                    pos_list.append(rect)

        # -------------------- check fuzzy logic case ------------------------
        if en_fuzzy and not pos_list:
            max_match = 0
            for k in range(5):
                for i in range(1, len(ocr_json)-k-1):
                    comb_text = ocr_json[i]['description'].lower() + ' ' + ocr_json[i + 1]['description'].lower()
                    if constant.no_hint_list.__contains__(comb_text):
                        continue

                    text_comb = ''
                    for j in range(k):
                        text_comb += ocr_json[i+j]['description']
                        if j == 0:
                            rect = self.get_rect(ocr_json[i]['boundingPoly']['vertices'])
                        else:
                            rect_next = self.get_rect(ocr_json[i+j]['boundingPoly']['vertices'])
                            rect = self.class_func.merge_rect(rect, rect_next)

                    match = fuzz.ratio(text_comb.lower(), dst_word.lower())
                    if max_match < match:
                        max_match = match
                        max_pos = rect

            if max_match > 82:
                pos_list.append(max_pos)

        if pos_list:
            return pos_list
        else:
            return None

    @staticmethod
    def get_rect(parent):

        if 'x' in parent[0]:
            x1 = parent[0]['x']
        else:
            x1 = 0

        if 'y' in parent[0]:
            y1 = parent[0]['y']
        else:
            y1 = 0

        if 'x' in parent[2]:
            x2 = parent[2]['x']
        else:
            x2 = 0

        if 'y' in parent[2]:
            y2 = parent[2]['y']
        else:
            y2 = 0

        return [x1, y1, x2, y2]

    @staticmethod
    def expand_region(old_region, proximity_type, margin, rx, ry):

        [x1, y1, x2, y2] = old_region

        if proximity_type == 'above_text':
            nx1 = x1 - int(margin * (x2 - x1))
            nx2 = x2 + max(int(margin * (x2 - x1)), 130)
            ny1 = y2 + ry / 30  # for 5 pixel
            ny2 = 10000
        elif proximity_type == 'below_text':
            nx1 = x1 - int(margin * (x2 - x1))
            nx2 = x2 + int(margin * (x2 - x1))
            ny1 = 1
            ny2 = y1 - ry / 30
        elif proximity_type == 'same_line_prefix':
            nx1 = x2 + rx / 30
            nx2 = 10000
            ny1 = y1 - int(margin * (y2 - y1))
            ny2 = y2 + int(margin * (y2 - y1))
        else:
            nx1 = 1
            nx2 = x1 - rx / 30
            ny1 = y1 - int(margin * (y2 - y1))
            ny2 = y2 + int(margin * (y2 - y1))

        return [nx1, ny1, nx2, ny2]

    def get_data(self, ocr_json, proximity, data_type, rate_x, rate_y, en_fuzzy=True):

        hint_pos_list = []
        key_pos = []
        for i in range(len(proximity)):
            # ---------------------- Get the [proximity][text] region ---------------------------
            data_type_pos = self.get_position(proximity[i]['text'], ocr_json, data_type, en_fuzzy=en_fuzzy)
            if data_type_pos is None:
                continue

            # --------------- Expand the above region using [proximity][type] --------------------
            new_region1 = []
            new_region2 = []
            hint_pos1 = []
            hint_pos2 = []
            for j in range(len(data_type_pos)):
                # check if other words are in left and right margin of hint pos, and store it hint_pos1 and 2
                proximity_type = proximity[i]['type']
                hint_rect = data_type_pos[j]

                if proximity_type == 'same_line_suffix':
                    margin_rect = [hint_rect[2] + 2, hint_rect[1] + 2, hint_rect[2] + int(rate_x/5), hint_rect[3] - 2]
                else:
                    margin_rect = [hint_rect[0] - int(rate_x/4), hint_rect[1] + 2, hint_rect[0] - 2, hint_rect[3] - 2]

                f_overlap = False
                for k in range(1, len(ocr_json)):
                    if self.class_func.check_overlap_rect(margin_rect, self.class_func.get_rect_ocr_data(ocr_json, k)):
                        f_overlap = True
                        break

                if f_overlap:
                    hint_pos2.append([proximity[i]['type'], hint_rect])
                else:
                    hint_pos1.append([proximity[i]['type'], hint_rect])

                # expand region of hint pos
                if proximity_type == 'above_text' or proximity_type == 'below_text':
                    margin = 1.2
                else:
                    margin = 0.0

                region = self.expand_region(hint_rect, proximity_type, margin, rate_x, rate_y)
                if f_overlap:
                    new_region2.append(region)
                else:
                    new_region1.append(region)

            if len(hint_pos1) > 0:
                hint_pos_list.append(hint_pos1)
            else:
                hint_pos_list.append(hint_pos2)

            if len(new_region1) > 0:
                key_pos.append(new_region1)
            else:
                key_pos.append(new_region2)

        if len(key_pos) == 0:
            return '', '', '', ''

        # ----------------- Get new matching result from expanded region ---------------------
        new_text = ''
        new_text_list = []
        new_text_pos = []
        rect_prev = None

        for i in range(1, len(ocr_json)):
            pos = self.get_rect(ocr_json[i]['boundingPoly']['vertices'])

            if len(key_pos) == 1:       # ---------- in case of proximity hint is 1
                f_match = False
                for j in range(len(key_pos[0])):
                    if self.class_func.check_overlap_rect(key_pos[0][j], pos):
                        f_match = True
                        break

            elif len(key_pos) == 2:       # ---------- in case of proximity hint is more tan 2
                f_match = False
                for k1, k2 in itertools.product(range(len(key_pos[0])), range(len(key_pos[1]))):
                    if self.class_func.check_overlap_rect(key_pos[0][k1], pos) and \
                            self.class_func.check_overlap_rect(key_pos[1][k2], pos):
                        f_match = True
                        break

            elif len(key_pos) == 3:       # ---------- in case of proximity hint is more tan 3
                f_match = False
                for k1, k2, k3 in itertools.product(range(len(key_pos[0])), range(len(key_pos[1])),
                                                    range(len(key_pos[2]))):
                    if self.class_func.check_overlap_rect(key_pos[0][k1], pos) and \
                            self.class_func.check_overlap_rect(key_pos[1][k2], pos) and \
                            self.class_func.check_overlap_rect(key_pos[2][k3], pos):
                        f_match = True
                        break

            elif len(key_pos) == 4:       # ---------- in case of proximity hint is more tan 4
                f_match = False
                for k1, k2, k3, k4 in itertools.product(range(len(key_pos[0])), range(len(key_pos[1])),
                                                        range(len(key_pos[2])), range(len(key_pos[3]))):
                    if self.class_func.check_overlap_rect(key_pos[0][k1], pos) and \
                            self.class_func.check_overlap_rect(key_pos[1][k2], pos) and \
                            self.class_func.check_overlap_rect(key_pos[2][k3], pos) and \
                            self.class_func.check_overlap_rect(key_pos[3][k4], pos):
                        f_match = True
                        break

            else:
                f_match = False

            if f_match:
                text_item = ocr_json[i]['description']
                rect = ocr_json[i]['boundingPoly']['vertices']

                x1 = self.class_func.get_field_int(rect[0], 'x')
                y1 = self.class_func.get_field_int(rect[0], 'y')

                if rect_prev is None:
                    x2 = 0
                    y2 = 0
                else:
                    x2 = self.class_func.get_field_int(rect_prev[1], 'x')
                    y2 = self.class_func.get_field_int(rect_prev[0], 'y')

                rect_prev = rect

                if abs(x1 - x2) < rate_x / 2.5 and abs(y1 - y2) < rate_y / 30:
                    if text_item == '/' or (len(new_text) > 0 and new_text[-1] == '/'):
                        new_text += text_item
                    elif text_item == '-' or (len(new_text) > 0 and new_text[-1] == '-'):
                        new_text += text_item
                    elif text_item == '.' or (len(new_text) > 0 and new_text[-1] == '.'):
                        new_text += text_item
                    elif text_item == ',' or (len(new_text) > 0 and new_text[-1] == ','):
                        new_text += text_item
                    elif len(new_text) > 0 and new_text[-1] == '$':
                        new_text += text_item
                    else:
                        new_text += (' ' + text_item)
                else:
                    if new_text == '':
                        new_text += text_item
                    else:
                        new_text += ('\n' + text_item)

                new_text_list.append(text_item)
                new_text_pos.append(pos)

        return new_text, hint_pos_list, new_text_list, new_text_pos
