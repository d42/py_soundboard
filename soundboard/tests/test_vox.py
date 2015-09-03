from soundboard.vox import voxify


def test_numbers():
    assert voxify('130') == ['vox/1.wav', 'vox/hundred.wav', 'vox/30.wav']
