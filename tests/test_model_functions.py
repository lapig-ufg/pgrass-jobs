from pydantic import PyObject
from app.model.functions import get_id, get_id_by_lon_lat
from app.db import PyObjectId


def test_get_id():
    assert get_id("1") == PyObjectId('2f169f9b4e6a1024752209cd')
    


def test_get_id_by_lon_lat():
    assert get_id_by_lon_lat(1,1,1) == PyObjectId('19709ae8c5c93e1548c80ecf')
    assert get_id_by_lon_lat(0.1,0.1,1234) == PyObjectId('6d6196b34fdec20edef184b8')



def test_get_id_by_lon_lat_5_and_9_after_the_comma():
    assert get_id_by_lon_lat(1.11111,1.11111,1234) == PyObjectId('976347ab42193823d31c0c39')
    assert get_id_by_lon_lat(1.111111111,1.111111111,1234) == PyObjectId('976347ab42193823d31c0c39')