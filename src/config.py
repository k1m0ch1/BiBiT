from os import environ

_ = environ.get

PRIME_TIME=_("PRIME_TIME", ["09:00", "19:00"])
SCRAPPING_TIME=_("SCRAPPING_TIME", ["00:30", "06:45", "16:45"])
GENERATE_TIME=_("GENERATE_TIME", ["01:00", "07:30", "17:30"])
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
}