from llmware.library import Library
from llmware.prompts import Prompt, Sources
from llmware.retrieval import Query

import streamlit as st

import os
import sys

sys.path.insert(0, os.getcwd())

from Utils import get_stored_files, get_stored_libraries


ACCOUNT_NAME = 'lecture_tool'
SUMMARIZER_MODEL = 'slim-summary-tool'


#
# Summarizes specified file in specified library.
#
# Performs a text query for the topic, which can be an empty string.
#
# Uses the SUMMARIZER_MODEL defined above to generate a summary.
#
@st.cache_data(show_spinner=False)
def summarize_file(library_name, filename, topic):
    # Load in appropriate library
    library = Library().load_library(library_name, account_name=ACCOUNT_NAME)
    print('\nupdate: library card - ', library.get_library_card())

    # Create Query object
    query = Query(library)
    
    # Load in appropriate model
    summarizer_prompter = Prompt().load_model(SUMMARIZER_MODEL, temperature=0.0, sample=False)

    # Access all text blocks corresponding to specified file if no topic is provided
    if topic == '':
        # Filter out text chunks by filename
        print('\nupdate: no topic provided, summarizing entire library')
        query_results = query.apply_custom_filter(query.get_whole_library(), {'file_source': filename})

        # Change key in query results for compatibility with RAG call
        for result in query_results:
            result['text'] = result['text_search']
            del result['text_search']
    # Access the text blocks corresponding to the specified file and topic
    else:
        # Perform text query for the topic, then filter out text blocks by filename
        print('\nupdate: topic provided, performing text query')
        query_results = query.apply_custom_filter(query.text_query(topic), {'file_source': filename})

    print('\nupdate: correct library chunks - ', query_results)

    # Pass in appropriate text blocks as source to the model
    sources = Sources(summarizer_prompter).package_source(query_results, aggregate_source=True)
    print('\nupdate: sources - ', sources)

    # Prompt the model for a summary
    print('\nupdate: summarizing in process')
    response = summarizer_prompter.prompt_with_source('key points', first_source_only=False, verbose=True)
    print('\nupdate: response - ', response)

    # Create a list of only the unique points generated by the model
    key_points = []
    for resp in response:
        for point in resp["llm_response"]:
            if point not in key_points:
                if point.strip():
                    if not point.strip().startswith("Not Found"):
                        key_points.append('- ' + point)

    return key_points


#
# Main block for GUI logic.
#
if __name__ == '__main__':
    st.title('Summarize your lectures')

    st.write('### Prompt info')

    library_name = st.selectbox(
        'Select the library:',
        tuple(get_stored_libraries())
    )

    if library_name:
        filename = st.selectbox(
            'Select the file:',
            tuple(get_stored_files(library_name))
        )

        topic = st.text_input('Optionally enter a topic to summarize:')

    if (st.button('Summarize')):
        with st.spinner('Summarizing transcript... don\'t leave this page!'):
            response = summarize_file(library_name, filename, topic)

        st.write('### Summary')

        for point in response:
            st.write(point)
