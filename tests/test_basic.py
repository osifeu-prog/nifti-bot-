import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_env_variables():
    assert os.getenv('BOT_TOKEN') is not None
    assert os.getenv('DATABASE_URL') is not None
    assert os.getenv('TON_WALLET') is not None

def test_nifti_core_imports():
    import nifti_core as core
    assert hasattr(core, 'create_pool')
    assert hasattr(core, 'load_lang')

def test_get_level():
    from server import get_level
    assert get_level(0) == "⚪ Newbie"
    assert get_level(1) == "🥉 Bronze"
    assert get_level(5) == "🥈 Silver"
    assert get_level(15) == "🥇 Gold"
    assert get_level(50) == "💎 Diamond"
