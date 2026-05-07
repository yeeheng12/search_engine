# GenAI Usage Declaration — COMP3011 Coursework 2

## Tool Used

Claude (Anthropic), accessed through claude.ai.

## Purpose of GenAI Use

Generative AI was used as a development support tool during the project. It helped with:

- planning the initial project structure;
- drafting early boilerplate for HTTP requests and BeautifulSoup parsing;
- suggesting possible edge cases for testing;
- explaining errors when tests failed;
- reviewing alternative data structures for the inverted index.

The AI was not used as a substitute for understanding the coursework requirements. All generated suggestions were checked against the assignment brief and the relevant lecture material before being accepted or modified.

## Where GenAI Was Helpful

GenAI was most useful during the early planning stage. It helped organise the project into separate crawler, indexer, search, and command-line interface components. This made the implementation easier to test and explain.

It also helped identify practical implementation details, such as using a `visited` set to avoid crawling duplicate URLs and using mocked HTTP responses in the crawler tests. This allowed the crawler logic to be tested without repeatedly sending requests to the live website.

## Where GenAI Was Incorrect or Unhelpful

Some AI suggestions were incomplete or unsuitable for the coursework requirements.

First, an early suggestion stored full URLs directly inside the inverted index. I changed this to use document IDs instead, with a separate document table mapping IDs to URLs. This better matches the lecture model of posting lists and makes the index structure cleaner and more efficient.

Second, the AI suggested extracting both targeted quote content and the full page body text. This caused some words to be indexed twice, inflating frequency statistics. I identified this problem during review and corrected the extraction logic so that quote text, authors, and tags are indexed once, with a fallback only where necessary.

Third, one suggested crawler test expected the politeness delay to be called, but the mocked HTML contained no links. As a result, the crawler only visited one page and the delay was never triggered. I debugged this manually by changing the mock page structure so the test actually exercised multiple requests.

## Manual Verification and Changes

The final implementation was manually reviewed and tested. In particular, I verified that:

- the crawler respects the required politeness delay;
- duplicate URLs are not crawled repeatedly;
- the inverted index stores document IDs, frequencies, and word positions;
- search is case-insensitive;
- multi-word `find` queries return pages containing all query terms;
- missing words, empty queries, and missing index files are handled gracefully;
- the saved index can be loaded again and queried successfully.

I also added and ran unit tests for the crawler, indexer, and search components to check both normal behaviour and edge cases.

## Effect on Learning

Using GenAI made the initial development process faster, especially for scaffolding and test ideas. However, it also showed the importance of not accepting AI-generated code without inspection. Several suggestions had to be corrected because they did not fully match the lecture material or the assignment requirements.

The most useful learning came from reviewing and debugging the AI suggestions. In particular, I developed a clearer understanding of why an inverted index should use posting lists, why document ID mapping is useful, why tokenisation must be consistent between indexing and querying, and why frequency counts must not be distorted by duplicate text extraction.

## Academic Integrity Statement

All GenAI use has been declared above. The final code was reviewed, tested, and corrected by me. I understand the implementation and can explain the design decisions, including the crawler structure, inverted index format, storage approach, search behaviour, and testing strategy.