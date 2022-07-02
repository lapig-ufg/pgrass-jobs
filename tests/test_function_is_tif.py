from app.fuctions import is_tif


def test_is_tif():
    assert is_tif('/HOME/FILE.TIF') == True
    assert is_tif('/HOME/FILE.TIFF') == True
    assert is_tif('/HOME/FILE.tif') == True
    assert is_tif('/HOME/FILE.tiff') == True
    assert is_tif('http://HOME/FILE.tiff') == True
    assert is_tif('ftp://HOME/FILE.tiff') == True
    assert is_tif('ftp://HOME/FILE.txt')  == False
    
   
