from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
from pathlib import Path
import re
from collections import Counter
import io

app = Flask(__name__)

# Common English stop words to exclude from word frequency analysis
STOP_WORDS = {
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i', 'it', 'for',
    'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at', 'this', 'but', 'his', 'by',
    'from', 'they', 'we', 'say', 'her', 'she', 'or', 'an', 'will', 'my', 'one', 'all',
    'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who', 'get',
    'which', 'go', 'me', 'when', 'make', 'can', 'like', 'time', 'no', 'just', 'him',
    'know', 'take', 'people', 'into', 'year', 'your', 'good', 'some', 'could', 'them',
    'see', 'other', 'than', 'then', 'now', 'look', 'only', 'come', 'its', 'over', 'think',
    'also', 'back', 'after', 'use', 'two', 'how', 'our', 'work', 'first', 'well', 'way',
    'even', 'new', 'want', 'because', 'any', 'these', 'give', 'day', 'most', 'us', 'is',
    'was', 'are', 'been', 'has', 'had', 'were', 'said', 'did', 'having', 'may', 'should',
    'am', 'being', 'does', 'done', 'using', 'based', 'through'
}

# Global state
state = {
    'df': None,
    'filtered_df': None,
    'title_col': None,
    'kept_papers': [],  # Papers marked as "keep" (Y)
    'rejected_papers': [],  # Papers marked as "reject" (N)
    'swipe_index': 0  # Current position in swipe queue
}


class NLPFilter:
    """Simple NLP filtering utilities"""

    @staticmethod
    def keyword_filter(text, keywords, match_all=False):
        """Filter based on keyword presence"""
        if pd.isna(text):
            return False

        text_lower = str(text).lower()
        matches = [kw.lower() in text_lower for kw in keywords]

        if match_all:
            return all(matches)
        else:
            return any(matches)

    @staticmethod
    def exclude_filter(text, exclude_words):
        """Exclude papers containing certain words"""
        if pd.isna(text):
            return True

        text_lower = str(text).lower()
        return not any(word.lower() in text_lower for word in exclude_words)

    @staticmethod
    def length_filter(text, min_words=0, max_words=1000):
        """Filter based on title length"""
        if pd.isna(text):
            return False

        word_count = len(str(text).split())
        return min_words <= word_count <= max_words

    @staticmethod
    def get_word_frequencies(texts, top_n=50):
        """Get most common words from titles, excluding stop words"""
        all_words = []
        for text in texts:
            if not pd.isna(text):
                words = re.findall(r'\b[a-zA-Z]{3,}\b', str(text).lower())
                # Filter out stop words
                words = [w for w in words if w not in STOP_WORDS]
                all_words.extend(words)

        return Counter(all_words).most_common(top_n)


def load_data():
    """Load the processed data"""
    data_path = Path("../data")

    # Check for processed file first
    processed_file = data_path / "processed_papers.csv"
    if processed_file.exists():
        return pd.read_csv(processed_file)

    # Otherwise look for original file
    csv_files = list(data_path.glob("scopus_export*.csv"))
    if csv_files:
        return pd.read_csv(csv_files[0])

    return None


def find_title_column(df):
    """Identify the title column"""
    for col in df.columns:
        if 'title' in col.lower():
            return col
    return df.columns[0]


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/load', methods=['GET'])
def api_load():
    """Load the dataset"""
    if state['df'] is None:
        state['df'] = load_data()
        if state['df'] is not None:
            state['filtered_df'] = state['df'].copy()
            state['title_col'] = find_title_column(state['df'])

    if state['df'] is None:
        return jsonify({'error': 'No data file found'}), 404

    return jsonify({
        'total': len(state['df']),
        'filtered': len(state['filtered_df']),
        'title_column': state['title_col'],
        'columns': list(state['df'].columns)
    })


@app.route('/api/filter', methods=['POST'])
def api_filter():
    """Apply filters to the dataset"""
    data = request.json

    include_keywords = [k.strip() for k in data.get('include_keywords', '').split('\n') if k.strip()]
    exclude_keywords = [k.strip() for k in data.get('exclude_keywords', '').split('\n') if k.strip()]
    match_all = data.get('match_all', False)
    min_words = data.get('min_words', 0)
    max_words = data.get('max_words', 100)

    filtered_df = state['df'].copy()

    # Apply inclusion filter
    if include_keywords:
        filtered_df = filtered_df[
            filtered_df[state['title_col']].apply(
                lambda x: NLPFilter.keyword_filter(x, include_keywords, match_all)
            )
        ]

    # Apply exclusion filter
    if exclude_keywords:
        filtered_df = filtered_df[
            filtered_df[state['title_col']].apply(
                lambda x: NLPFilter.exclude_filter(x, exclude_keywords)
            )
        ]

    # Apply length filter
    filtered_df = filtered_df[
        filtered_df[state['title_col']].apply(
            lambda x: NLPFilter.length_filter(x, min_words, max_words)
        )
    ]

    state['filtered_df'] = filtered_df

    return jsonify({
        'total': len(state['df']),
        'filtered': len(state['filtered_df']),
        'removed': len(state['df']) - len(state['filtered_df'])
    })


@app.route('/api/reset', methods=['POST'])
def api_reset():
    """Reset filters"""
    state['filtered_df'] = state['df'].copy()

    return jsonify({
        'total': len(state['df']),
        'filtered': len(state['filtered_df'])
    })


@app.route('/api/preview', methods=['GET'])
def api_preview():
    """Get preview of filtered data"""
    page = request.args.get('page', 0, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')

    df = state['filtered_df'].copy()

    if search:
        df = df[df[state['title_col']].str.contains(search, case=False, na=False)]

    start = page * per_page
    end = start + per_page

    return jsonify({
        'total': len(df),
        'page': page,
        'per_page': per_page,
        'data': df.iloc[start:end].to_dict('records'),
        'columns': list(df.columns)
    })


@app.route('/api/word_frequencies', methods=['GET'])
def api_word_frequencies():
    """Get word frequency analysis"""
    top_n = request.args.get('top_n', 30, type=int)

    if state['filtered_df'] is None or len(state['filtered_df']) == 0:
        return jsonify({'frequencies': []})

    frequencies = NLPFilter.get_word_frequencies(
        state['filtered_df'][state['title_col']],
        top_n=top_n
    )

    return jsonify({
        'frequencies': [{'word': word, 'count': count} for word, count in frequencies]
    })


@app.route('/api/export', methods=['GET'])
def api_export():
    """Export filtered data as CSV"""
    if state['filtered_df'] is None or len(state['filtered_df']) == 0:
        return jsonify({'error': 'No data to export'}), 400

    # Create CSV in memory
    output = io.StringIO()
    state['filtered_df'].to_csv(output, index=False)
    output.seek(0)

    # Convert to bytes
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)

    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='filtered_papers.csv'
    )


@app.route('/api/remove_rows', methods=['POST'])
def api_remove_rows():
    """Remove specific rows by index"""
    data = request.json
    indices = data.get('indices', [])

    if indices:
        state['filtered_df'] = state['filtered_df'].drop(indices)

    return jsonify({
        'removed': len(indices),
        'remaining': len(state['filtered_df'])
    })


@app.route('/api/swipe/current', methods=['GET'])
def api_swipe_current():
    """Get the current paper for swiping"""
    if state['filtered_df'] is None or len(state['filtered_df']) == 0:
        return jsonify({'error': 'No data loaded'}), 400

    # Reset index if we've gone past the end
    if state['swipe_index'] >= len(state['filtered_df']):
        return jsonify({
            'done': True,
            'kept': len(state['kept_papers']),
            'rejected': len(state['rejected_papers'])
        })

    current_row = state['filtered_df'].iloc[state['swipe_index']]

    return jsonify({
        'index': state['swipe_index'],
        'total': len(state['filtered_df']),
        'title': current_row[state['title_col']],
        'row_id': int(current_row.name) if hasattr(current_row, 'name') else state['swipe_index'],
        'kept_count': len(state['kept_papers']),
        'rejected_count': len(state['rejected_papers'])
    })


@app.route('/api/swipe/decision', methods=['POST'])
def api_swipe_decision():
    """Record a swipe decision (Y=keep, N=reject)"""
    data = request.json
    decision = data.get('decision')  # 'Y' or 'N'

    if state['filtered_df'] is None or state['swipe_index'] >= len(state['filtered_df']):
        return jsonify({'error': 'No more papers'}), 400

    current_row = state['filtered_df'].iloc[state['swipe_index']]
    paper_info = {
        'index': int(current_row.name) if hasattr(current_row, 'name') else state['swipe_index'],
        'title': current_row[state['title_col']],
        'data': current_row.to_dict()
    }

    if decision == 'Y':
        state['kept_papers'].append(paper_info)
    elif decision == 'N':
        state['rejected_papers'].append(paper_info)

    # Move to next paper
    state['swipe_index'] += 1

    # Check if we're done
    done = state['swipe_index'] >= len(state['filtered_df'])

    return jsonify({
        'success': True,
        'next_index': state['swipe_index'],
        'done': done,
        'kept_count': len(state['kept_papers']),
        'rejected_count': len(state['rejected_papers'])
    })


@app.route('/api/swipe/reset', methods=['POST'])
def api_swipe_reset():
    """Reset swipe session"""
    state['swipe_index'] = 0
    state['kept_papers'] = []
    state['rejected_papers'] = []

    return jsonify({
        'success': True,
        'message': 'Swipe session reset'
    })


@app.route('/api/swipe/export_kept', methods=['GET'])
def api_swipe_export_kept():
    """Export kept papers as CSV"""
    if not state['kept_papers']:
        return jsonify({'error': 'No kept papers to export'}), 400

    # Create DataFrame from kept papers
    kept_df = pd.DataFrame([p['data'] for p in state['kept_papers']])

    # Create CSV in memory
    output = io.StringIO()
    kept_df.to_csv(output, index=False)
    output.seek(0)

    # Convert to bytes
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)

    return send_file(
        mem,
        mimetype='text/csv',
        as_attachment=True,
        download_name='kept_papers.csv'
    )


if __name__ == '__main__':
    print("=" * 60)
    print("📄 Scopus Paper Filter - Flask UI")
    print("=" * 60)
    print("\nStarting server...")
    print("Open your browser and go to: http://localhost:5000")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)
