
import os


corvina_username = os.environ['FACTORYAL_CORVINA_USERNAME']
corvina_client_secret = os.environ['FACTORYAL_CORVINA_CLIENT_SECRET']

corvina_org = os.environ['FACTORYAL_CORVINA_ORG']
corvina_suffix = os.environ.get('FACTORYAL_CORVINA_SUFFIX', '.io')
corvina_prefix = os.environ['FACTORYAL_CORVINA_PREFIX']

# Debug part!!!
tree_path_separator_char = os.environ.get('FACTORYAL_TREE_PATH_SEPARATOR', '.')
