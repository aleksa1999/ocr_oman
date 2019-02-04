
from Categorization import FuncMl
from Categorization import constant


class DateExtractor:

    def __init__(self):
        """
            class initial function
        """
        self.class_func = FuncMl()

    @staticmethod
    def get_pre_digit(text, reverse=False):

        if text == '':
            return text

        if reverse:
            text = text[::-1]

        if not text.isdigit() and text[0].isdigit():
            i = 0
            for i in range(len(text)):
                if not text[i].isdigit():
                    break

            text = text[:i]

        if reverse:
            text = text[::-1]

        return text

    @staticmethod
    def split_text(text):
        """
            Split the text as digital and chars. for example:
            '14Jul18' => ['14', 'Jul', '18']
        """
        char_prev_st = 0
        char_list = ''
        txt_date = []
        for i in range(len(text)):
            if text[i].isdigit():
                char_st = 1
            elif text[i].isalpha():
                char_st = 2
            else:
                char_st = 3

            if char_prev_st != char_st and char_list != '':
                txt_date.append(char_list)
                char_list = ''

            char_list += text[i]
            char_prev_st = char_st

        txt_date.append(char_list)

        return txt_date

    def is_date(self, text, country='US'):

        # if text == 'Jun16/18':
        #     print "1"

        month_list = constant.month_list
        if country == 'NL':
            month_list_full = constant.month_list_full_NL
        else:
            month_list_full = constant.month_list_full

        score = 10

        if text.__contains__('/'):
            txt_date = text.split('/')
        elif text.__contains__('-'):
            txt_date = text.split('-')
        elif text.__contains__('.') or text.__contains__(','):
            txt_date = text.replace('.', ' ').replace(',', ' ').split()
            score -= 1
        elif text.__contains__("'"):
            txt_date = text.split("'")
        else:
            txt_date = self.split_text(text)

        if len(txt_date) == 1:
            score -= 2
            if txt_date[0].isdigit():
                if len(text) == 6:
                    txt_date[0] = text[0]
                    txt_date.append(text[1])
                    txt_date.append(text[2:])
                elif len(text) == 7:
                    if text[0] == '0':
                        txt_date[0] = text[0:2]
                        txt_date.append(text[2])
                    else:
                        txt_date[0] = text[0]
                        txt_date.append(text[1:3])
                    txt_date.append(text[3:])
                elif len(text) == 8:
                    txt_date[0] = text[0:2]
                    txt_date.append(text[2:4])
                    txt_date.append(text[4:])
                elif len(text) == 10:
                    txt_date[0] = text[0:2]
                    txt_date.append(text[3:5])
                    txt_date.append(text[6:])
                else:
                    return None
            else:
                if len(text) == 10:     # 'DECO1,2017'
                    if text[0:3].isalpha() and text[3:5].replace('O', '0').isdigit() and \
                            text[6:].isdigit() and text[5] == ',':
                        score -= 1
                        txt_date[0] = text[0:3]
                        txt_date.append(text[3:5].replace('O', '0'))
                        txt_date.append(text[6:])
                    else:
                        return None
                else:
                    return None
        elif len(txt_date) == 2:
            score -= 1
            temp1 = txt_date[0]
            temp2 = txt_date[1]

            if txt_date[0].isdigit():
                if len(temp2) <= 4:
                    if len(temp1) == 4:     # 0722 => 07, 22
                        txt_date[0] = temp1[0:2]
                        txt_date[1] = temp1[2:]
                    elif len(temp1) == 3:   # 072 => 07, 2
                        txt_date[0] = temp1[0:2]
                        txt_date[1] = temp1[2]
                    elif len(temp1) == 2:   # 72 => 7, 2
                        txt_date[0] = temp1[0]
                        txt_date[1] = temp1[1]
                    elif len(temp1) == 5 and temp1[2] == '1':       # 07l22 => 07, 22
                        txt_date[0] = temp1[0:2]
                        txt_date[1] = temp1[3:]
                    else:
                        return None

                    txt_date.append(temp2)
                else:
                    txt_date[0] = temp1
                    if len(temp2) == 6:     # '11 212017' => '11,21,2017'
                        txt_date[1] = temp2[0:2]
                        txt_date.append(temp2[2:])
                    else:
                        return None
            elif txt_date[0] != '' and txt_date[0][0].isalpha() and txt_date[0][-1].isdigit():   # 'May04'
                for i in range(len(temp1)):
                    if temp1[i].isdigit():
                        t1 = temp1[:i].lower()
                        t2 = temp1[i:]
                        if (month_list_full.__contains__(t1) or month_list.__contains__(t1)) and t2.isdigit():
                            score += 1
                            txt_date[0] = t1
                            txt_date[1] = t2
                            txt_date.append(temp2)
                            break
                        else:
                            return None

                if len(txt_date) == 2:
                    return None

            else:
                return None

        elif len(txt_date) != 3:
            return None

        txt_date[0] = txt_date[0].split(':')[-1]

        # ----------- collecting digit from mix of digit and string -----------
        txt_date[0] = self.get_pre_digit(txt_date[0], reverse=True)
        txt_date[2] = self.get_pre_digit(txt_date[2])

        if txt_date[1] == '1st':
            txt_date[1] = '1'
        elif txt_date[1] == '2nd':
            txt_date[1] = '2'
        elif txt_date[1] == '3rd':
            txt_date[1] = '3'
        elif txt_date[1][:-2].isdigit() and txt_date[1][-2:] == 'th':
            txt_date[1] = txt_date[1][:-2]

        # ----------------------------- extract the date --------------------------
        data_month = 0
        data_day = 0

        if len(txt_date[0]) == 4 and len(txt_date[1]) == 2 and len(txt_date[2]) == 2:   # case of yyyy/mm/dd
            if txt_date[0].isdigit() and txt_date[1].isdigit() and txt_date[2].isdigit():
                data_year = int(txt_date[0])
                data_month = int(txt_date[1])
                data_day = int(txt_date[2])

                if not (1900 < data_year < 2100 and 1 <= data_month <= 12 and 1 <= data_day <= 31):
                    return None

            else:
                return None

        else:
            # -------------------------- Checking of year -------------------------
            if txt_date[2].isdigit():
                if 1900 <= int(txt_date[2]) <= 2100:
                    data_year = int(txt_date[2])
                elif len(txt_date[2]) == 2 and int(txt_date[2]) < 50:
                    data_year = int(txt_date[2]) + 2000
                    score -= 1
                else:
                    return None
            elif txt_date[2][:-1].isdigit():
                score -= 1
                if 1900 <= int(txt_date[2][:-1]) <= 2100:
                    data_year = int(txt_date[2][:-1])
                elif len(txt_date[2][:-1]) == 2 and int(txt_date[2][:-1]) < 50:
                    data_year = int(txt_date[2][:-1]) + 2000
                    score -= 1
                else:
                    return None
            else:
                return None

            find_md = True
            if txt_date[1].isdigit():     # case of m/d/y
                # -------------------------- Checking of day -------------------------
                if 0 < int(txt_date[1]) <= 31:
                    data_day = int(txt_date[1])
                else:
                    find_md = False

                # -------------------------- Checking of month -------------------------
                if txt_date[0].isdigit():
                    if 0 < int(txt_date[0]) <= 12 and find_md:
                        if data_day < 13 and (country == 'INDIA' or country == 'NL'):
                            data_month = data_day
                            data_day = int(txt_date[0])
                        else:
                            data_month = int(txt_date[0])
                    else:
                        find_md = False
                elif month_list.__contains__(txt_date[0].lower()):
                    data_month = month_list.index(txt_date[0].lower()) + 1
                    score += 1
                elif month_list_full.__contains__(txt_date[0].lower()):
                    data_month = month_list_full.index(txt_date[0].lower()) + 1
                    score += 1
                else:
                    find_md = False
            else:
                find_md = False

            if not find_md:       # case of d/m/y
                if txt_date[0].isdigit():
                    # -------------------------- Checking of day -------------------------
                    if 0 < int(txt_date[0]) <= 31:
                        data_day = int(txt_date[0])
                    else:
                        return None

                    # -------------------------- Checking of month -------------------------
                    if txt_date[1].isdigit() and 0 < int(txt_date[1]) <= 12:
                        data_month = int(txt_date[1])
                    elif month_list.__contains__(txt_date[1].lower()):
                        data_month = month_list.index(txt_date[1].lower()) + 1
                    elif month_list_full.__contains__(txt_date[1].lower()):
                        data_month = month_list_full.index(txt_date[1].lower()) + 1
                    else:
                        return None

                else:
                    return None

        if country == 'NL':
            # ret = '%02d/%02d/%04d' % (data_day, data_month, data_year)
            ret = '%04d-%02d-%02d' % (data_year, data_month, data_day)
        else:
            ret = '%02d/%02d/%04d' % (data_month, data_day, data_year)

        return [ret, score]

    def extract(self, text, country='US'):
        text_line_list = text.replace("'", ' ').splitlines()
        result_value = []
        result_score = []

        for comb_lines in range(2):
            # -------------- First check one lines, and if not detect, check combination of 2 lines ------------
            for line_ind in range(len(text_line_list) - comb_lines):
                if comb_lines == 0:
                    text_list = text_line_list[line_ind].split()
                elif comb_lines == 1:
                    text_list = text_line_list[line_ind].split() + text_line_list[line_ind + 1].split()
                else:
                    text_list = []

                # ---------------- for single word --------------------
                for text_item in text_list:
                    ret = self.is_date(text_item, country)
                    if ret is not None:
                        result_value.append(ret[0])
                        result_score.append(ret[1])

                # ---------------- for combination of 2 words('04/20/ 2017') --------------------
                for i in range(len(text_list)-1):
                    ret = self.is_date(text_list[i] + ' ' + text_list[i+1], country)
                    if ret is not None:
                        result_value.append(ret[0])
                        result_score.append(ret[1])

                # ---------------- for combination of 2 words('Sep 1,2017') --------------------
                for i in range(len(text_list)-1):
                    ret = self.is_date(text_list[i] + '/' + text_list[i+1].replace(',', '/'), country)
                    if ret is not None:
                        result_value.append(ret[0])
                        result_score.append(ret[1])

                # ----------- for combination of 3 words ---------------
                for i in range(len(text_list)-2):

                    new_text = self.class_func.text_clean(text_list[i]) + '/' + \
                               self.class_func.text_clean(text_list[i+1]) + '/' + \
                               self.class_func.text_clean(text_list[i+2])

                    ret = self.is_date(new_text, country)
                    if ret is not None:
                        result_value.append(ret[0])
                        result_score.append(ret[1])

            if len(result_value) > 0:
                max_score = max(result_score)
                ret_date = []
                for i in range(len(result_score)):
                    if result_score[i] == max_score > 7:
                        ret_date.append(result_value[i])

                # error correction
                if len(ret_date) == 2:  # ['6/13/2018', '6/13/2013']
                    if ret_date[0][:-1] == ret_date[1][:-1]:
                        if ret_date[0][-1] == '8' and ret_date[1][-1] == '3':
                            ret_date = [ret_date[0][:-1] + '8']

                return ret_date

        return []
