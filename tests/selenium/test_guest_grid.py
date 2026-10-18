"""Selenium Grid 4 Parallel Test Suite for Guest Web Player (Section 6.2.3)."""
import os
import time
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

GRID_URL = os.getenv("SELENIUM_GRID_URL", "http://localhost:4444/wd/hub")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")


@pytest.fixture(scope="function")
def driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    try:
        d = webdriver.Remote(command_executor=GRID_URL, options=options)
    except Exception:
        # Fallback to local chrome if grid is unavailable during offline debug
        d = webdriver.Chrome(options=options)
    d.implicitly_wait(5)
    yield d
    d.quit()


def test_qr_resolution_and_zero_friction_load(driver):
    """Test 1: QR short URL redirects to /web/matches/match-m1/live and renders video + score without login modal."""
    driver.get(f"{BASE_URL}/q/m1-live")

    # Assert redirected URL
    WebDriverWait(driver, 5).until(lambda d: "/web/matches/match-m1/live" in d.current_url)

    # Assert mandatory data-testid elements visible
    video_player = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="guest-video-player"]'))
    )
    score_banner = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="live-score-banner"]'))
    )
    assert video_player.is_displayed()
    assert score_banner.is_displayed()

    # Zero login modal on initial load
    login_modals = driver.find_elements(By.CSS_SELECTOR, '[data-testid="progressive-auth-modal"]')
    assert len(login_modals) == 0 or not login_modals[0].is_displayed()


def test_guest_write_block_and_progressive_modal(driver):
    """Test 2: Guest write attempt opens progressive-auth-modal and blocks message broadcast."""
    driver.get(f"{BASE_URL}/web/matches/match-m1/live")

    chat_input = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="chat-input-field"]'))
    )
    chat_send = driver.find_element(By.CSS_SELECTOR, '[data-testid="chat-send-btn"]')

    test_msg = "Hello from unauthorized guest"
    chat_input.send_keys(test_msg)
    chat_send.click()

    # Message must NOT be appended to chat-message-list
    time.sleep(0.5)
    chat_list = driver.find_element(By.CSS_SELECTOR, '[data-testid="chat-message-list"]')
    assert test_msg not in chat_list.text

    # Progressive registration modal must be visible
    modal = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="progressive-auth-modal"]'))
    )
    assert modal.is_displayed()


def test_guest_cart_staging_and_score_sync(driver):
    """Test 3: Guest stages merchandise in cart and sees real-time score update."""
    driver.get(f"{BASE_URL}/web/matches/match-m1/live")

    # Click add-to-guest-cart-btn
    add_btn = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, '[data-testid="add-to-guest-cart-btn"]'))
    )
    add_btn.click()

    # Verify guest-cart-count increments to 1
    cart_count = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, '[data-testid="guest-cart-count"]'))
    )
    assert cart_count.text.strip() in {"1", "(1)"}

    # Trigger a real-time score event via POST /audit/v1/events
    event_payload = {
        "event_id": f"ev-{int(time.time()*1000)}",
        "match_id": "match-m1",
        "team_id": "club-alpha-1",
        "player_id": "player-alpha-1",
        "event_type": "goal",
        "points": 1,
        "timestamp_iso": "2026-10-18T10:00:00Z"
    }
    resp = requests.post(f"{BASE_URL}/audit/v1/events", json=event_payload, timeout=3)
    assert resp.status_code in {200, 201}

    # Assert score banner updates in browser DOM
    WebDriverWait(driver, 5).until(
        lambda d: "2" in d.find_element(By.CSS_SELECTOR, '[data-testid="live-score-banner"]').text
    )

