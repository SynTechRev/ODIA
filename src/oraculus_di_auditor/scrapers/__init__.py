"""External-source scrapers for the O.D.I.A. ingestion pipeline.

Each scraper is purpose-built for one specific external archive that
publishes records O.D.I.A. needs to analyse but does not surface as
PDF uploads. The scrapers are deliberately polite (robots.txt-aware,
rate-limited, identifying User-Agent) and run only on explicit
operator invocation.

Current scrapers:

  - ``tcdao_archive``      v1 yearly category archive scraper for
                           tulareda.org press releases.
  - ``tcdao_archive_v2``   v2 enhancements: monthly-archive
                           dropdown discovery, 2022 path-variant
                           handling, gap-band absence-record emission
                           (see Cross-Entity Protocol section 5.3
                           "Leave No Stone Unturned").

Both scrapers depend on ``requests`` and ``beautifulsoup4``. Importing
this package is lightweight; the heavy network and parsing imports
live inside the submodules and are not pulled in until the scraper is
actually invoked.
"""
