import time

modules = [
    ('pandas', 'import pandas'),
    ('src.data_loader', 'from src.data_loader import DataLoader'),
    ('src.brand_normalizer', 'from src.brand_normalizer import BrandNormalizer'),
    ('src.brand_learner', 'from src.brand_learner import BrandLearner'),
    ('src.classifier_learner', 'from src.classifier_learner import ClassifierLearner'),
    ('src.description_parser', 'from src.description_parser import DescriptionParser'),
    ('src.desc_generator', 'from src.desc_generator import DescriptionGenerator'),
    ('src.web_sourcing', 'from src.web_sourcing import WebEnricher'),
    ('src.attribute_grammars', 'from src.attribute_grammars import extract_grammar_attributes'),
    ('src.desc_engine', 'from src.desc_engine import generate_mobile_desc'),
]

for name, stmt in modules:
    t = time.time()
    exec(stmt)
    print('%s: %.3fs' % (name, time.time() - t))
