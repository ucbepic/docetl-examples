import json
import openreview
import pandas as pd
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os
import argparse
from datetime import datetime
import random
load_dotenv()

def download_conference_reviews(venue_id, username, password, output_file):
    """
    Download all reviews for a specific conference from OpenReview using venue information
    
    Parameters:
    venue_id (str): The venue ID (e.g., 'ICLR.cc/2024/Conference')
    username (str): OpenReview username
    password (str): OpenReview password
    output_file (str): Output CSV file name
    
    Returns:
    pandas.DataFrame: DataFrame containing all reviews
    """
    try:
        # Initialize the client
        client = openreview.api.OpenReviewClient(
            baseurl='https://api2.openreview.net',
            username=username,
            password=password
        )
        
        # Get venue information and submission name
        venue_group = client.get_group(venue_id)
        submission_name = venue_group.content['submission_name']['value']
        
        # Get all submissions with their replies
        submissions = client.get_all_notes(
            invitation=f'{venue_id}/-/{submission_name}',
            details='replies'
        )
        print(f'Found {len(submissions)} submissions')
        
        reviews_data = []
        
        # Get review name from venue group
        review_name = venue_group.content['review_name']['value']
        
        # Process submissions and their reviews with progress bar
        for submission in tqdm(submissions, desc="Processing submissions"):
            submission_title = submission.content['title']
            submission_number = submission.number
            
            # Get reviews for this submission
            submission_reviews = [openreview.api.Note.from_json(reply) for reply in submission.details['replies']
                                if f'{venue_id}/{submission_name}{submission_number}/-/{review_name}' in reply['invitations']]
            
            # Process each review for this submission
            for review in submission_reviews:
                review_data = {
                    'paper_id': submission_number,
                    'paper_title': submission_title.get('value', 'N/A'),
                    'review_id': review.id,
                    'rating': review.content.get('rating', {}).get('value', 'N/A'),
                    'confidence': review.content.get('confidence', {}).get('value', 'N/A'),
                    'summary': review.content.get('summary', {}).get('value', 'N/A'),
                    'soundness': review.content.get('soundness', {}).get('value', 'N/A'),
                    'presentation': review.content.get('presentation', {}).get('value', 'N/A'),
                    'contribution': review.content.get('contribution', {}).get('value', 'N/A'),
                    'strengths': review.content.get('strengths', {}).get('value', 'N/A'),
                    'weaknesses': review.content.get('weaknesses', {}).get('value', 'N/A'),
                    'questions': review.content.get('questions', {}).get('value', 'N/A'),
                    'ethics_flag': review.content.get('flag_for_ethics_review', {}).get('value', 'N/A'),
                    'code_of_conduct': review.content.get('code_of_conduct', {}).get('value', 'N/A'),
                    'timestamp': review.tcdate
                }
                reviews_data.append(review_data)
        
        print(f'Found {len(reviews_data)} total reviews')
        
        # Convert to DataFrame
        df = pd.DataFrame(reviews_data)
        
        # Save to CSV with escaping special characters
        df.to_csv(output_file, index=False, escapechar='\\')
        print(f'Successfully saved {len(reviews_data)} reviews to {output_file}')
        
        return df
        
    except Exception as e:
        print(f'Error occurred: {str(e)}')
        return None

def read_reviews_to_json(csv_file, reviews_per_doc=50, max_docs=100, json_file='reviews.json'):
    """
    Read conference reviews from CSV file and convert to JSON format with batched reviews.
    
    Args:
        csv_file (str): Path to the CSV file containing reviews
        reviews_per_doc (int): Number of reviews to include in each document
        max_docs (int): Maximum number of documents to create
        json_file (str): Path to the output JSON file
        
    Returns:
        dict: Reviews data in JSON format with batched reviews
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_file)
        
        # Group reviews by paper_id
        paper_groups = df.groupby('paper_id')
        
        # Get unique paper IDs
        unique_papers = list(paper_groups.groups.keys())
        
        # Randomly shuffle papers
        random.shuffle(unique_papers)
        
        # Format all reviews while keeping track of individual review count
        all_reviews = []  # Will store tuples of (paper_id, review_count, formatted_review)
        
        for paper_id in unique_papers:
            paper_reviews = paper_groups.get_group(paper_id)
            paper_title = paper_reviews.iloc[0]['paper_title']
            
            # Format all reviews for this paper together
            paper_review_strs = []
            for idx, (_, review) in enumerate(paper_reviews.iterrows(), 1):
                review_str = (
                    f"Review #{idx}:\n"
                    f"Rating: {review['rating']}\n"
                    f"Confidence: {review['confidence']}\n\n"
                    f"Summary:\n{review['summary']}\n\n"
                    f"Soundness: {review['soundness']}\n"
                    f"Presentation: {review['presentation']}\n"
                    f"Contribution: {review['contribution']}\n\n"
                    f"Strengths:\n{review['strengths']}\n\n"
                    f"Weaknesses:\n{review['weaknesses']}\n\n"
                    f"Questions:\n{review['questions']}\n\n"
                    f"Ethics Flag: {review['ethics_flag']}\n"
                    "-------------------------------------------\n"
                )
                paper_review_strs.append(review_str)
            
            # Combine all reviews for this paper
            combined_review = (
                f"Paper {paper_id}: {paper_title}\n\n"
                + "\n".join(paper_review_strs)
                + "==========================================\n"
            )
            all_reviews.append((paper_id, len(paper_reviews), combined_review))
        
        # Create documents with the right number of reviews
        reviews_json = []
        current_doc = []
        current_review_count = 0
        total_reviews = 0
        
        for paper_id, review_count, formatted_review in all_reviews:
            # Add this paper's reviews to current document
            current_doc.append(formatted_review)
            current_review_count += review_count
            total_reviews += review_count
            
            # If adding this paper's reviews would exceed reviews_per_doc,
            # save current document and start a new one
            if current_review_count > reviews_per_doc:
                if current_doc:  # Save current document if it has any reviews
                    reviews_json.append({"content": "\n".join(current_doc)})
                    if len(reviews_json) >= max_docs:  # Stop if we've reached max_docs
                        break
                    current_doc = []
                    current_review_count = 0
        
        
        # Save to JSON file
        with open(json_file, 'w') as f:
            json.dump(reviews_json, f)
        
        print(f'Successfully saved {len(reviews_json)} docs to {json_file}')
        print(f'Total reviews included: {total_reviews}')
        print(f'Average reviews per document: ~{total_reviews // len(reviews_json)}')
        
    except Exception as e:
        print(f'Error reading CSV file: {str(e)}')
        return None



if __name__ == "__main__":
    default_year = 2025
    parser = argparse.ArgumentParser(description='Download and process ICLR conference reviews')
    parser.add_argument('--year', type=int, default=default_year,
                      help='Conference year (defaults to next year)')
    parser.add_argument('--reviews-per-doc', type=int, 
                      default=int(os.getenv('REVIEWS_PER_DOC', '50')),
                      help='Number of reviews per document (default: 50)')
    parser.add_argument('--max-docs', type=int,
                      default=int(os.getenv('MAX_DOCS', '100')),
                      help='Maximum number of documents to create (default: 100)')
    parser.add_argument('--csv-file', type=str, 
                      default=f'conference_reviews_{default_year}.csv',
                      help='CSV file to read/write reviews (default: conference_reviews.csv)')
    parser.add_argument('--json-file', type=str,
                      default=f'reviews_{default_year}.json',
                      help='JSON output file (default: reviews.json)')
    parser.add_argument('--download', action='store_true',
                      help='Download fresh reviews from OpenReview')
    
    args = parser.parse_args()
    
    # Construct venue ID using the year
    VENUE_ID = f'ICLR.cc/{args.year}/Conference'
    USERNAME = os.getenv('OPENREVIEW_USERNAME')
    PASSWORD = os.getenv('OPENREVIEW_PASSWORD')
    
    if args.download:
        if not USERNAME or not PASSWORD:
            raise ValueError("OPENREVIEW_USERNAME and OPENREVIEW_PASSWORD must be set in .env file")
            
        reviews_df = download_conference_reviews(
            venue_id=VENUE_ID,
            username=USERNAME,
            password=PASSWORD,
            output_file=args.csv_file
        )
        
        if reviews_df is None:
            print("Failed to download reviews")
            exit(1)
    
    # Convert CSV to JSON with specified number of reviews per document
    read_reviews_to_json(
        args.csv_file,
        reviews_per_doc=args.reviews_per_doc,
        max_docs=args.max_docs,
        json_file=args.json_file
    )