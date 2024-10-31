import unittest
from unittest.mock import patch, MagicMock
from RedditFunction.reddit import fetch_and_store_reddit_posts

class TestRedditFunction(unittest.TestCase):

    @patch('RedditFunction.reddit.MongoClient')
    @patch('RedditFunction.reddit.praw.Reddit')
    def test_fetch_and_store_reddit_posts(self, MockReddit, MockMongoClient):
        # Mocking Reddit API
        mock_reddit_instance = MockReddit.return_value
        mock_subreddit = MagicMock()
        mock_post_1 = MagicMock(title="Test Post 1", url="http://example.com/1", score=100, created_utc=1633036800, subreddit=MagicMock(display_name="test"), author=MagicMock(name="test_author"), selftext="Sample text")
        mock_post_2 = MagicMock(title="Test Post 2", url="http://example.com/2", score=200, created_utc=1633036801, subreddit=MagicMock(display_name="test"), author=MagicMock(name="test_author_2"), selftext="Another sample text")
        mock_subreddit.hot.return_value = [mock_post_1, mock_post_2]
        mock_reddit_instance.subreddit.return_value = mock_subreddit

        # Mocking MongoDB
        mock_collection = MagicMock()
        MockMongoClient.return_value.__getitem__.return_value = {"RedditPosts": mock_collection}

        # Call the function
        fetch_and_store_reddit_posts('test_subreddit', post_limit=2)

        # Verifying if insert_many was called and inspect what was passed
        self.assertTrue(mock_collection.insert_many.called, "insert_many was not called on MongoDB collection")
        self.assertEqual(mock_collection.insert_many.call_count, 1, "insert_many was not called exactly once")

        # Ensure correct number of posts are passed to insert_many
        args, _ = mock_collection.insert_many.call_args
        inserted_data = args[0]
        self.assertEqual(len(inserted_data), 2, "Expected two posts to be inserted")

        # Verify inserted data content
        self.assertEqual(inserted_data[0]['title'], "Test Post 1")
        self.assertEqual(inserted_data[1]['title'], "Test Post 2")

if __name__ == '__main__':
    unittest.main()
