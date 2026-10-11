import csv
import os
import time
import requests

from difflib import SequenceMatcher
from pathlib import Path
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_FILE = "data/metadata/paper_list_final_37.csv"
OUTPUT_FILE = "data/metadata/openalex_verification.csv"

OPENALEX_URL = "https://api.openalex.org/works"

# Load .env
load_dotenv()

OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY")


# ============================================================
# CHECK API KEY
# ============================================================

if not OPENALEX_API_KEY:

    raise RuntimeError(
        "OPENALEX_API_KEY not found.\n"
        "Add it to your .env file."
    )


# ============================================================
# TITLE NORMALIZATION
# ============================================================

def normalize_title(title):

    title = title.lower().strip()

    # Remove common punctuation
    replacements = [
        ":", ",", ".", ";", "!", "?",
        "(", ")", "[", "]", "{", "}",
        "-", "–", "—"
    ]

    for char in replacements:
        title = title.replace(char, " ")

    # Remove duplicate spaces
    title = " ".join(title.split())

    return title


# ============================================================
# TITLE SIMILARITY
# ============================================================

def similarity(title1, title2):

    title1 = normalize_title(title1)
    title2 = normalize_title(title2)

    return SequenceMatcher(
        None,
        title1,
        title2
    ).ratio()


# ============================================================
# OPENALEX REQUEST
# ============================================================

def search_openalex(title):

    params = {
        "search": title,
        "per-page": 10
    }

    headers = {
        "Authorization": f"Bearer {OPENALEX_API_KEY}"
    }

    max_retries = 5

    for attempt in range(max_retries):

        try:

            response = requests.get(
                OPENALEX_URL,
                params=params,
                headers=headers,
                timeout=30
            )


            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if response.status_code == 200:

                data = response.json()

                return data.get(
                    "results",
                    []
                )


            # ------------------------------------------------
            # RATE LIMIT
            # ------------------------------------------------

            if response.status_code == 429:

                retry_after = response.headers.get(
                    "Retry-After"
                )

                if retry_after:

                    wait_time = int(
                        retry_after
                    )

                else:

                    wait_time = 2 ** attempt


                print(
                    f"429 rate limit. "
                    f"Waiting {wait_time} seconds..."
                )

                time.sleep(
                    wait_time
                )

                continue


            # ------------------------------------------------
            # SERVER ERROR
            # ------------------------------------------------

            if response.status_code >= 500:

                wait_time = 2 ** attempt

                print(
                    f"OpenAlex server error "
                    f"{response.status_code}. "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(
                    wait_time
                )

                continue


            # ------------------------------------------------
            # OTHER ERROR
            # ------------------------------------------------

            print(
                f"OpenAlex HTTP error "
                f"{response.status_code}"
            )

            print(
                response.text[:500]
            )

            return None


        except requests.RequestException as error:

            wait_time = 2 ** attempt

            print(
                f"Request error: {error}"
            )

            print(
                f"Retrying in {wait_time}s..."
            )

            time.sleep(
                wait_time
            )


    print(
        "OpenAlex request failed "
        "after all retries."
    )

    return None


# ============================================================
# FIND BEST MATCH
# ============================================================

def find_best_match(
    original_title,
    results
):

    if not results:

        return None, 0


    best_result = None
    best_score = 0


    for result in results:

        openalex_title = result.get(
            "title",
            ""
        )

        if not openalex_title:

            continue


        score = similarity(
            original_title,
            openalex_title
        )


        if score > best_score:

            best_score = score
            best_result = result


    return best_result, best_score


# ============================================================
# MATCH STATUS
# ============================================================

def get_status(score):

    if score >= 0.95:

        return "STRONG"

    elif score >= 0.80:

        return "REVIEW"

    else:

        return "WEAK"


# ============================================================
# GET AUTHORS
# ============================================================

def get_authors(result):

    authors = []


    for authorship in result.get(
        "authorships",
        []
    ):

        author = authorship.get(
            "author",
            {}
        )

        name = author.get(
            "display_name"
        )

        if name:

            authors.append(name)


    return "; ".join(authors)


# ============================================================
# GET URL
# ============================================================

def get_url(result):

    location = result.get(
        "primary_location"
    )

    if not location:

        return ""


    return location.get(
        "landing_page_url",
        ""
    )


# ============================================================
# MAIN
# ============================================================

def main():

    input_path = Path(
        INPUT_FILE
    )

    output_path = Path(
        OUTPUT_FILE
    )


    # --------------------------------------------------------
    # CHECK INPUT
    # --------------------------------------------------------

    if not input_path.exists():

        raise FileNotFoundError(
            f"Input file not found: "
            f"{input_path}"
        )


    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )


    # --------------------------------------------------------
    # READ PAPERS
    # --------------------------------------------------------

    with open(
        input_path,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        reader = csv.DictReader(file)

        papers = list(reader)


    print(
        f"Found {len(papers)} papers."
    )


    # --------------------------------------------------------
    # OUTPUT COLUMNS
    # --------------------------------------------------------

    fieldnames = [

        "paper_id",
        "pdf_filename",
        "title",
        "domain",

        "openalex_id",
        "openalex_title",

        "authors",
        "year",

        "doi",
        "url",

        "match_score",
        "status"
    ]


    # --------------------------------------------------------
    # COUNTERS
    # --------------------------------------------------------

    strong = 0
    review = 0
    weak = 0
    not_found = 0
    api_failed = 0


    # --------------------------------------------------------
    # CREATE OUTPUT
    # --------------------------------------------------------

    with open(
        output_path,
        "w",
        encoding="utf-8",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()


        # ====================================================
        # PROCESS EACH PAPER
        # ====================================================

        for index, paper in enumerate(
            papers,
            start=1
        ):

            paper_id = paper[
                "paper_id"
            ]

            title = paper[
                "title"
            ]


            print()
            print("=" * 60)

            print(
                f"[{index}/{len(papers)}] "
                f"{paper_id}"
            )

            print(
                f"Title: {title}"
            )


            # ------------------------------------------------
            # SEARCH
            # ------------------------------------------------

            results = search_openalex(
                title
            )


            # ------------------------------------------------
            # API FAILURE
            # ------------------------------------------------

            if results is None:

                print(
                    "Status: API_FAILED"
                )

                api_failed += 1


                writer.writerow({

                    "paper_id":
                        paper["paper_id"],

                    "pdf_filename":
                        paper["pdf_filename"],

                    "title":
                        paper["title"],

                    "domain":
                        paper["domain"],

                    "openalex_id":
                        "",

                    "openalex_title":
                        "",

                    "authors":
                        "",

                    "year":
                        "",

                    "doi":
                        "",

                    "url":
                        "",

                    "match_score":
                        "",

                    "status":
                        "API_FAILED"
                })


                file.flush()

                continue


            # ------------------------------------------------
            # NO RESULTS
            # ------------------------------------------------

            if not results:

                print(
                    "Status: NOT_FOUND"
                )

                not_found += 1


                writer.writerow({

                    "paper_id":
                        paper["paper_id"],

                    "pdf_filename":
                        paper["pdf_filename"],

                    "title":
                        paper["title"],

                    "domain":
                        paper["domain"],

                    "openalex_id":
                        "",

                    "openalex_title":
                        "",

                    "authors":
                        "",

                    "year":
                        "",

                    "doi":
                        "",

                    "url":
                        "",

                    "match_score":
                        "",

                    "status":
                        "NOT_FOUND"
                })


                file.flush()

                continue


            # ------------------------------------------------
            # BEST MATCH
            # ------------------------------------------------

            best_result, score = find_best_match(
                title,
                results
            )


            if best_result is None:

                print(
                    "Status: NOT_FOUND"
                )

                not_found += 1

                continue


            # ------------------------------------------------
            # MATCH STATUS
            # ------------------------------------------------

            status = get_status(
                score
            )


            print(
                "OpenAlex title:",
                best_result.get(
                    "title",
                    ""
                )
            )

            print(
                f"Match score: "
                f"{score:.3f}"
            )

            print(
                f"Status: {status}"
            )


            # ------------------------------------------------
            # COUNTERS
            # ------------------------------------------------

            if status == "STRONG":

                strong += 1

            elif status == "REVIEW":

                review += 1

            else:

                weak += 1


            # ------------------------------------------------
            # EXTRACT METADATA
            # ------------------------------------------------

            authors = get_authors(
                best_result
            )

            url = get_url(
                best_result
            )


            # ------------------------------------------------
            # WRITE RESULT
            # ------------------------------------------------

            writer.writerow({

                "paper_id":
                    paper["paper_id"],

                "pdf_filename":
                    paper["pdf_filename"],

                "title":
                    paper["title"],

                "domain":
                    paper["domain"],

                "openalex_id":
                    best_result.get(
                        "id",
                        ""
                    ),

                "openalex_title":
                    best_result.get(
                        "title",
                        ""
                    ),

                "authors":
                    authors,

                "year":
                    best_result.get(
                        "publication_year",
                        ""
                    ),

                "doi":
                    best_result.get(
                        "doi",
                        ""
                    ),

                "url":
                    url,

                "match_score":
                    round(
                        score,
                        3
                    ),

                "status":
                    status
            })


            # Save immediately
            file.flush()


            # Small delay between requests
            time.sleep(1)


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print("OPENALEX VERIFICATION COMPLETE")
    print("=" * 60)

    print(
        f"Total papers : {len(papers)}"
    )

    print(
        f"Strong       : {strong}"
    )

    print(
        f"Review       : {review}"
    )

    print(
        f"Weak         : {weak}"
    )

    print(
        f"Not found    : {not_found}"
    )

    print(
        f"API failed   : {api_failed}"
    )

    print()
    print(
        "Output:",
        output_path
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()