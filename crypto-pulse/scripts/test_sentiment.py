from transformers import pipeline
import time

def test_sentiment():
    print("Loading FinBERT model... (This might take a moment the first time)")
    start = time.time()
    try:
        sentiment_pipe = pipeline("text-classification", model="ProsusAI/finbert")
        print(f"Model loaded in {time.time() - start:.2f} seconds.")
        
        texts = [
            "Bitcoin price hits new all-time high, investors celebrate!",
            "Major exchange hack leads to massive sell-off and fear.",
            "The market remains stable with low volatility today."
        ]
        
        for text in texts:
            result = sentiment_pipe(text)[0]
            print(f"Text: {text}")
            print(f"  Sentiment: {result['label']} (Score: {result['score']:.4f})")
            
    except Exception as e:
        print(f"Error during sentiment test: {e}")

if __name__ == "__main__":
    test_sentiment()
