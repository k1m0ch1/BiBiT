import unittest

class TestEnvironmentVariable(unittest.TestCase):
    
    def testEnvVarNotEmpty(self):
        from src import config
        if config.TWITTER_NOTIFICATION:
            print(f"twitter notification is enabled")
            assert len(config.TWITTER_API_KEY) > 0, "env TWITTER_API_KEY is empty"
            assert len(config.TWITTER_API_SECRET_KEY) > 0, "env TWITTER_API_SECRET_KEY is empty"
            assert len(config.TWITTER_ACCESS_TOKEN) > 0, "env TWITTER_ACCESS_TOKEN is empty"
            assert len(config.TWITTER_ACCESS_TOKEN_SECRET) > 0, "env TWITTER_ACCESS_TOKEN_SECRET is empty"
        if config.DISCORD_NOTIFICATION:
            print(f"discord notification is enabled")
            assert len(config.DISCORD_WEBHOOK_URL) > 0, "env DISCORD_WEBHOOK_URL is empty"

if __name__ == '__main__':
    unittest.main()