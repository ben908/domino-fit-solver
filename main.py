import time
import sys
import os
import math

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


def load_driver():
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-infobars')

    chrome_binary_path = os.path.join(os.getcwd(), "chrome-linux64", "chrome")
    chromedriver_path = os.path.join(os.getcwd(), "chromedriver-linux64", "chromedriver")
    options.binary_location = chrome_binary_path


    driver = webdriver.Chrome(options=options)

    # options.add_argument("--headless")
    driver.get("https://dominofit.isotropic.us/")
    driver.maximize_window()

    return driver

def go_to_start_state(driver):
    try:
        elem = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "iPrompt"))
        )
    finally:
        elem.click()


def click_to_start(driver):
    try:
        elem = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".gameOverlayText"))
        )
    finally:
        size = elem.size
        webdriver.ActionChains(driver).move_to_element_with_offset(elem, size['width']//2, size['height']//2).click().perform()

def click_to_next(driver):
    driver.find_element(By.ID, "aCGNextBtn").click()

# only 1 id in number cells, but at different locations depending on the number and in svgs
def find_id(elem):
    if elem.get_attribute("id"):
        t_res = elem.get_attribute("id")
        if t_res[0] == "_":
            return t_res[1]
        else:
            return ""
    res = ""
    for child in elem.find_elements(By.XPATH, "*"):
        res += find_id(child)
    return res

def read_board(driver, size):
    board = []
    column_counts = []
    row_counts = []

    for i in range(2, 2+size, 1):
        value = find_id(driver.find_element(By.XPATH, f'/html/body/div[8]/div[3]/div[2]/div[1]/div/div[1]/div[{i}]/div')).replace("_", "")
        column_counts.append(int(value))


    for i in range(2, 2+size, 1):
        value = find_id(driver.find_element(By.XPATH, f'/html/body/div[8]/div[3]/div[2]/div[1]/div/div[{i}]/div[1]/div')).replace("_", "")
        row_counts.append(int(value))

    board = [[0] * size for _ in range(size)]
    board_elements = [[None] * size for _ in range(size)]

    for row in range(2, 2+size, 1):
        for col in range(2, 2+size, 1):
            elem = driver.find_element(By.XPATH, f'/html/body/div[8]/div[3]/div[2]/div[1]/div/div[{row}]/div[{col}]')
            board_elements[row-2][col-2] = elem
            elems = elem.find_elements(By.XPATH, "*")
            if len(elems) == 0:
                continue
            classes = elems[0].get_attribute("class")
            if "sqBlockShadow" in classes:
                board[row-2][col-2] = -math.inf

    return board, board_elements, column_counts, row_counts


# Can either do a visual solve or programmatic solve
# domino1: 1        domino2: 2 0
#          0

# changes to these checks can make the solver more efficient
def is_valid_row(board, cur_row, row_sums):
    s = 0
    size = len(board)
    for col in range(size): # check the row so go through each column
        if board[cur_row][col] >= 1:
            s += board[cur_row][col]
    return s <= row_sums[cur_row]

def is_valid_col(board, cur_col, col_sums):
    s = 0
    size = len(board)
    for row in range(size): # check the column, so go through each row
        if board[row][cur_col] >= 1:
            s += board[row][cur_col]

    return s <= col_sums[cur_col]

def is_valid(board, cur_col, cur_row, col_sums, row_sums):
    return is_valid_row(board, cur_row, row_sums) and is_valid_col(board, cur_col, col_sums)

def print_b(board):
    for r in board:
        print(r)

def true_solve(board, col_sums, row_sums):
    size = len(board)
    s = 0
    for cur_col in range(size):
        s = 0
        for row in range(size): # check the column, so go through each row
            if board[row][cur_col] >= 1:
                s += board[row][cur_col]

        if s != col_sums[cur_col]:
            return False

    for cur_row in range(size):
        s = 0
        for col in range(size): # check the row so go through each column
            if board[cur_row][col] >= 1:
                s += board[cur_row][col]
        if s != row_sums[cur_row]:
            return False

    return True

def solve(board, row_num, col_num, col_sums, row_sums):
    size = len(board)
    if col_num == size:
        col_num = 0
        row_num += 1
    if col_num == size-1 and row_num == size-1:
        return true_solve(board, col_sums, row_sums)

    if board[row_num][col_num] != 0: # is this space already in use
        if solve(board, row_num, col_num + 1, col_sums, row_sums):
            return True

    if row_num < size - 1 and board[row_num][col_num] == 0 and board[row_num+1][col_num] == 0:
        board[row_num][col_num] = 1
        board[row_num+1][col_num] = -1

        if is_valid(board, col_num, row_num, col_sums, row_sums): # check if most recent makes valid board
            if solve(board, row_num, col_num + 1, col_sums, row_sums): # if this "path" finds solution return
                return True

        # else backtrack
        board[row_num][col_num] = 0
        board[row_num+1][col_num] = 0

    # try to place other domino
    if col_num < size - 1 and board[row_num][col_num] == 0 and board[row_num][col_num+1] == 0:
        board[row_num][col_num] = -2
        board[row_num][col_num+1] = 2

        if is_valid(board, col_num, row_num, col_sums, row_sums):
            if solve(board, row_num , col_num + 1, col_sums, row_sums):
                return True

        board[row_num][col_num] = 0
        board[row_num][col_num+1] = 0


def get_domino_elems(driver):
    return (
        driver.find_element(By.XPATH, "/html/body/div[8]/div[3]/div[2]/div[2]/div[2]/div/div[1]"), # 1 domino
        driver.find_element(By.XPATH, "/html/body/div[8]/div[3]/div[2]/div[2]/div[2]/div/div[2]")  # 2 domino
    )

def individual_click(board_elem, val, dominos, driver):
    # click to correct domino
    dominos[val-1].click()
    # click on correct location
    webdriver.ActionChains(driver).move_to_element(board_elem).click().perform()


def board_click(board, board_elems, dominos, driver):
    size = len(board)

    for row in range(size):
        for col in range(size):
            if board[row][col] == -2 or board[row][col] == 1:
                individual_click(board_elems[row][col], abs(board[row][col]), dominos, driver)


if __name__ == '__main__':
    logging = True if len(sys.argv) == 2 and sys.argv[1] == '--log' else False
    if logging: print("Logging Enabled")

    driver = load_driver()
    go_to_start_state(driver)

    for size in [6, 7, 8]:
        driver.find_element(By.ID, f'gameSize{size}').click()
        for _ in range(3):
            click_to_start(driver)
            board, board_elems, cols_counts, rows_counts  = read_board(driver, size)

            if logging:
                print(f'Read Board')
                print_b(board)
                print(f'cols_counts: {cols_counts}, rows_counts: {rows_counts}')

            dominos = get_domino_elems(driver)
            solve(board, 0, 0, cols_counts, rows_counts)

            if logging:
                print(f'Solved Board:')
                print_b(board)
            board_click(board, board_elems, dominos, driver)

            time.sleep(5)
            if _ != 2:
                click_to_next(driver)

        webdriver.ActionChains(driver).move_to_element(driver.find_element(By.ID, "achievementsBtn")).click().perform()

    driver.quit()
    if logging: print("Solved All Boards")
