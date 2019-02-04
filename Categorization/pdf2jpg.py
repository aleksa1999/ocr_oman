
import os


def pdf2jpg_ppm(in_name, out_name, page=1, max_pdf_page=10):
    """
        convert the pdf file to jpg file
        page: None  => whole page
        page: 1~    => page number
    """

    command = "pdftoppm \"%s\" \"%s\" -jpeg" % (in_name, out_name)
    os.system(command)
    page_cnt = 0

    for file_name in os.listdir(os.curdir):
        if file_name.endswith(".jpg") and file_name.startswith(out_name):
            p_ind = int(file_name[len(out_name)+1:len(file_name)-4])

            if page == 0 and p_ind < max_pdf_page:
                page_cnt += 1
                os.rename(file_name, out_name + str(p_ind - 1) + '.jpg')

            elif p_ind == page:
                os.rename(file_name, out_name + '0.jpg')
                page_cnt = 1

            else:
                os.remove(file_name)

    return page_cnt
