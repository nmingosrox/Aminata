class CalendarFetcher:
    """
    CalendarFetcher collects economic calendar data from Forex Factory.
    """

    def __init__(self):
        """
        Initialize Chrome options and WebDriver.

        Returns:
            None
        """
        from selenium import webdriver

        options = webdriver.ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
        self.driver = webdriver.Chrome(options=options)

    def fetch_calendar(self) -> pd.DataFrame:
        """
        Fetch and parse Forex Factory calendar events.

        Returns:
            pd.DataFrame: DataFrame of calendar events.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from bs4 import BeautifulSoup

        print("[INFO] Navigating to Forex Factory...")
        self.driver.get("https://www.forexfactory.com/calendar")

        # Stage 1: Page load
        title = self.driver.title
        print(f"[INFO] Page title: {title}")
        assert_stage("Forex" in title or "Calendar" in title, "Page loaded successfully")

        # Stage 2: Cookie banner
        try:
            consent_btn = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            consent_btn.click()
            print("[INFO] Cookie banner accepted")
        except Exception:
            print("[INFO] No cookie banner detected")

        # Stage 3: Wait for table
        try:
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table.calendar__table"))
            )
            print("[INFO] Calendar table detected")
        except Exception as exc:
            raise RuntimeError("[FAIL] Calendar table not detected") from exc

        # Stage 4: Parse HTML
        soup = BeautifulSoup(self.driver.page_source, "html.parser")
        rows = soup.select("tr.calendar__row")
        print(f"[INFO] Found {len(rows)} rows in DOM")
        assert_stage(len(rows) > 0, "Extracted rows from calendar")

        # Stage 5: Extract events
        events: List[Dict[str, Any]] = []
        for row in rows:
            date = row.select_one("td.calendar__date")
            time = row.select_one("td.calendar__time")
            currency = row.select_one("td.calendar__currency")
            impact = row.select_one("td.calendar__impact")
            event = row.select_one("td.calendar__event")
            actual = row.select_one("td.calendar__actual")
            forecast = row.select_one("td.calendar__forecast")
            previous = row.select_one("td.calendar__previous")

            if not event or not event.get_text(strip=True):
                continue

            importance = impact.get_text(strip=True) if impact else "Unknown"

            events.append({
                "Date": date.get_text(strip=True) if date else None,
                "Time": time.get_text(strip=True) if time else None,
                "Currency": currency.get_text(strip=True) if currency else None,
                "Event": event.get_text(strip=True),
                "Importance": importance,
                "Actual": actual.get_text(strip=True) if actual else None,
                "Forecast": forecast.get_text(strip=True) if forecast else None,
                "Previous": previous.get_text(strip=True) if previous else None,
            })

        print(f"[INFO] Extracted {len(events)} events")
        assert_stage(len(events) > 0, "Events successfully extracted")

        return pd.DataFrame(events)

    def close(self) -> None:
        """
        Close the WebDriver.

        Returns:
            None
        """
        try:
            self.driver.quit()
        except Exception:
            pass

if __name__ == "__main__":
    calendar = CalendarFetcher()
    try:
        calendar_df = calendar.fetch_calendar()
        print(calendar_df.head())
    finally:
        calendar.close()
