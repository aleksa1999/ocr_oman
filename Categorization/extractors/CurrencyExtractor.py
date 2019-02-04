
from Categorization import FuncMl
import os


class CurrencyExtractor:

    def __init__(self):
        """
            class initial function
        """
        self.class_func = FuncMl()
        self.fix_json = self.class_func.load_json(os.path.join(self.class_func.my_dir, 'config/currency_fix.json'))

    def is_currency(self, text):

        # case of ocred incorrectly "," into "." such as    '$32.452.10',   => '$32452.10'
        #                           "." into "," such as    '$32,45'        => '$34.45'
        #                                                   '$164.04.'      => '$164.04'
        #                                                   '16.404:12USD'  => '$16404.12'

        # ------------------------ text pre-processing ------------------------
        text = text.replace(' ', '')

        if text[-3:] == 'USD':
            text = '$' + text[:len(text)-3].replace(':', '.')
        elif text[:3] == 'USD':
            text = '$' + text[3:len(text)]

        pos_dot = []
        for i in range(len(text) - 1):
            if text[i] == '.' or text[i] == ',':
                pos_dot.append(i)

        if len(pos_dot) > 0:
            if len(text[pos_dot[-1]+1:]) != 3 and text[pos_dot[-1]] == ',':
                char_last = '.'
            else:
                char_last = text[pos_dot[-1]]

            if char_last == '.':
                text = text[:pos_dot[-1]].replace(',', '').replace('.', '') + char_last + text[pos_dot[-1]+1:]
            else:
                text = text.replace(',', '').replace('.', '')

        # ----------------- Get valid text using '$' character ----------------
        #       ab$13.2 -> $13.2,         -$7.6 -> -$7.6
        # ---------------------------------------------------------------------
        if text.__contains__('$'):
            dollar_pos = text.find('$')
            if dollar_pos > 0 and text[dollar_pos - 1] == '-':
                text = text[dollar_pos - 1:]
            else:
                text = text[dollar_pos:]

        if text == '':
            return None

        # ------------------ Decide of positive or negative -------------------
        f_pos = False
        if len(text) > 2:
            if text[0] == '(' and text[-1] == ')':
                currency_data = text[1:-1]
            elif text[1] == '(' and text[-1] == ')':
                currency_data = text[0] + text[2:-1]
            elif text[-2:].upper() == 'CR':
                currency_data = text[:-2]
            elif text[0] == '-':
                currency_data = text[1:]
            elif text[-1] == '-':
                currency_data = text[:-1]
            else:
                currency_data = text
                f_pos = True
        else:
            currency_data = text
            f_pos = True

        # -------------------- Check existence dollar mark --------------------
        f_dollar = True
        if currency_data[0] == '$':
            currency_data = currency_data[1:]
            for i in range(len(currency_data)):
                if not currency_data[-1].isdigit():
                    currency_data = currency_data[:-1]
                else:
                    break
        elif currency_data[0] == 'S':
            currency_data = currency_data[1:]
        else:
            f_dollar = False

        # ------------------------- Convert to value --------------------------
        try:
            # some error correction ('99.G8 -> 99.08')
            if currency_data.__contains__('.'):
                for fix_key in self.fix_json:
                    if currency_data.count(str(fix_key)) == 1:
                        currency_data = currency_data.replace(str(fix_key), str(self.fix_json[fix_key]))

            ret = round(float(currency_data), 2)
            if not f_pos:
                ret = -ret

            ret = '{:.2f}'.format(ret)

            return [f_dollar, ret]

        except ValueError:
            return None

    def extract(self, text):

        text_list = text.split('\n')
        result_value = []
        result_value_dollar = []

        for i in range(len(text_list)):
            # ---------------- for single line --------------------
            ret = self.is_currency(text_list[i])
            if ret is not None:
                if ret[0]:
                    result_value_dollar.append(ret[1])
                else:
                    result_value.append(ret[1])

                continue

            # ------------------ for single word -------------------
            word_list = text_list[i].split()
            if len(word_list) == 1 or word_list.__contains__('%'):  # ignore `5.4%`, `(7%)`
                continue

            for j in range(len(word_list)):
                ret = self.is_currency(word_list[j])
                if ret is not None:
                    if ret[0]:
                        result_value_dollar.append(ret[1])
                    else:
                        result_value.append(ret[1])

        return result_value_dollar + result_value
