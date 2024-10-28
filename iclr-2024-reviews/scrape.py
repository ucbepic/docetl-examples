import openreview
import pandas as pd
import time
from tqdm import tqdm
from dotenv import load_dotenv
import os
load_dotenv()

def download_conference_reviews(venue_id, username, password, output_file='reviews.csv'):
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

if __name__ == "__main__":
    # Example usage
    VENUE_ID = 'ICLR.cc/2024/Conference'
    USERNAME = os.getenv('OPENREVIEW_USERNAME')
    PASSWORD = os.getenv('OPENREVIEW_PASSWORD')
    
    reviews_df = download_conference_reviews(
        venue_id=VENUE_ID,
        username=USERNAME,
        password=PASSWORD,
        output_file='conference_reviews.csv'
    )