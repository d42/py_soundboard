from soundboard.vox import voxify


def test_numbers():
    words = ['5', 'thousand', '1', 'hundred', '30']
    paths = ['vox/%s.wav' % w for w in words]
    assert voxify('5130') == paths
