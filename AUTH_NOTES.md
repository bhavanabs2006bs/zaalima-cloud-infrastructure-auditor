## API Rate-Limit Handling

Implemented basic retry and backoff logic.

Approach:
- Retry failed API calls up to 3 times.
- Wait 2 seconds before retrying.
- Stop after maximum retry attempts.

Purpose:
AWS APIs may temporarily reject requests due to throttling or rate limits.

Future Improvement:
Implement exponential backoff using retry libraries.