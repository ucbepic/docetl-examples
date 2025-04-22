# 1. Import the necessary functions
from edgar import *
import os
from datetime import datetime, timedelta

if __name__ == "__main__":
    # 2. Tell the SEC who you are
    set_identity("mike1@indigo.com")  # Replace with your actual email

    # 3. Create a directory to store downloads
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(curr_dir, "sec_8k_filings")
    os.makedirs(download_dir, exist_ok=True)

    # 4. Get all filings
    filings = get_filings(2025)

    # 5. Calculate date range for last 30 days
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    date_range = f"{start_date}:{end_date}"

    # 6. Filter filings by date range and form types
    filtered_filings = filings.filter(
        date=date_range,
        form=["8-K", "8-K12G3", "8-K15D5"]  # Filter by the specific form types
    )
    
    # Print the filings length
    print(f"Found {len(filtered_filings)} filings")

    # 7. Download the filings
    for i, filing in enumerate(filtered_filings):
        try:
            # Get the filing document
            print(filing)
            document = filing.text()
            
            # Create a filename using company name, CIK and filing date
            safe_name = "".join(c if c.isalnum() else "_" for c in filing.company)
            filename = f"{safe_name}_{filing.cik}_{filing.form}_{filing.filing_date}.txt"
            file_path = os.path.join(download_dir, filename)
            
            # Save the document
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(document)
            
            print(f"Downloaded ({i+1}): {filename}")
            
            # Add a small delay to be kind to SEC servers
            if i % 10 == 0:
                print(f"Processed {i+1} filings so far...")
        
        except Exception as e:
            print(f"Error downloading filing {filing.accession_number}: {str(e)}")

    print(f"Download complete. Total filings: {len(filtered_filings)}")