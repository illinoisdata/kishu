from kishu.diff import DiffAlgorithms, DiffAlgorithmResult, DiffHunk
def test_myre_diff():
    '''
    Test if idgraph can be created for a simple int.
    '''
    def is_matched(hunk: DiffHunk):
        return hunk.option == "Both"
    def get_content(hunk: DiffHunk):
        return hunk.content
    result = DiffAlgorithms.myre_diff(["a", "b","c","d","e"],["j","a", "b","d","e","f"])
    assert list(map(get_content,list(filter(is_matched,result.diff_hunks)))) == ["a", "b","d","e"]


def test_edr_diff():
    '''
    Test if idgraph can be created for a simple int.
    '''
    def is_matched(hunk: DiffHunk):
        return hunk.option == "Both"
    def get_content(hunk: DiffHunk):
        return hunk.content
    result = DiffAlgorithms.edr_diff(["a", "b\nc\nd\ne","c","d","e"],["j","a", "b\nd\ne","d","e","f"])
    assert list(map(get_content,list(filter(is_matched,result.diff_hunks)))) == ["a", "b\nc\nd\ne","d","e"]