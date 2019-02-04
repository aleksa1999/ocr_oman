
class StringExtractor:

    def __init__(self):
        pass

    @staticmethod
    def match_len(word, len_list, accept_char):

        if len_list is None:
            return True

        if accept_char is not None and accept_char.__contains__('space'):
            revised_word = word
        else:
            revised_word = word.replace(' ', '')

        if accept_char is not None and accept_char.__contains__('-'):
            pass
        else:
            revised_word = revised_word.replace('-', '')

        for i in range(len(len_list)):
            if len(revised_word) == len_list[i]:
                return True

        return False

    @staticmethod
    def match_char(word, char_lsit):

        if char_lsit is None:
            return True

        for i in range(len(word)):
            if word[i].isdigit():
                if not char_lsit.__contains__('digit'):
                    return False
            elif word[i].isalpha():
                if not char_lsit.__contains__('alphabet') and not char_lsit.__contains__('upper'):
                    return False
            elif word[i] == ' ':
                if not char_lsit.__contains__('space'):
                    return False
            elif not char_lsit.__contains__(word[i]):
                return False

        if 'digit' in char_lsit:
            f_digit = False
            for i in range(len(word)):
                if word[i].isdigit():
                    f_digit = True
                    break

            if not f_digit:
                return False

        if 'alphabet' in char_lsit:
            f_digit = False
            for i in range(len(word)):
                if word[i].isalpha():
                    f_digit = True
                    break

            if not f_digit:
                return False

        if 'upper' in char_lsit:
            f_upper = True
            for i in range(len(word)):
                if word[i].isalpha() and not word[i].isupper():
                    f_upper = False
                    break

            if not f_upper:
                return False

        if '.' in char_lsit and '.' not in word:
            return False

        return True

    @staticmethod
    def contain_string(text1, text2):
        if text1 is None:
            return False
        else:
            return text1.__contains__(text2)

    def extract(self, text, accept_char, accept_len, proximity_text):

        text_list = text.splitlines()
        result_value = []

        # ----------------------- check for individual words ------------------------
        for i in range(len(text_list)):
            if self.contain_string(accept_char, 'space'):
                find_ind = -1
                j = 0
                for j in range(len(proximity_text)):
                    find_ind = text_list[i].find(proximity_text[j])
                    if find_ind >= 0:
                        break

                if find_ind == -1:
                    new_text = text_list[i]
                else:
                    new_text = text_list[i][find_ind+len(proximity_text[j]):]

                # Remove unnecessary prefixes
                new_text = new_text.strip(" ").strip(":").strip(" ")
                if self.match_len(new_text, accept_len, accept_char) and self.match_char(new_text, accept_char):
                    result_value.append(new_text.strip())
                    
            else:
                word_list = text_list[i].replace('/', ' ').split()
                for word in word_list:
                    if self.match_len(word, accept_len, accept_char) and self.match_char(word, accept_char):
                        result_value.append(word)

        return result_value
