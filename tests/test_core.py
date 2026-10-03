import numpy as np
import pytest
from astra.geometry import backproject,transform,rigid_fit,icp
from astra.layout import measure,polygon_area
from astra.semantics import inverse_pixels,on_surface,ray_surface,scope_and_flags
from astra.io import photo_groups
from astra.evaluate import read_measurements


def test_depth_camera_units_and_transform():
    d=np.full((3,3),2.);K=np.array([[2.,0,1],[0,2,1],[0,0,1]])
    p=backproject(d,K);np.testing.assert_allclose(p[1,1],[0,0,2]);np.testing.assert_allclose(p[1,2],[1,0,2])
    T=np.eye(4);T[:3,3]=[1,2,3];np.testing.assert_allclose(transform(p[1],T),p[1]+[1,2,3])


def test_intrinsics_resize():
    d=np.ones((2,2));K=np.array([[4.,0,2],[0,4,2],[0,0,1]])
    np.testing.assert_allclose(backproject(d,K,(4,4))[1,1],[0,0,1])


def test_rigid_alignment_recovers_known_motion():
    rng=np.random.default_rng(4);a=rng.normal(size=(100,3));b=a+[.03,-.02,.01]
    T=rigid_fit(a,b);np.testing.assert_allclose(transform(a,T),b,atol=1e-8)
    T,info=icp(a,b);assert info['accepted'];np.testing.assert_allclose(T[:3,3],[.03,-.02,.01],atol=1e-6)


def test_rotation_pixels_roundtrip():
    # Raw pixel (20,30) in 100x80 rotates clockwise to (49,20).
    np.testing.assert_allclose(inverse_pixels([[49,20]],90,100,80),[[20,30]])


def test_metric_surface_projection_area():
    s={'id':'w','room_id':'r','kind':'wall','start':[-2,2],'end':[2,2],'floor_y':-1,'height':measure(3.)}
    K=np.array([[100.,0,100],[0,100,100],[0,0,1]]);pose=np.eye(4)
    uv,valid=on_surface(np.array([[75,75],[125,75],[125,125],[75,125]]),K,pose,s)
    assert valid.all();assert polygon_area(uv)==pytest.approx(1.)
    assert ray_surface([100,100],K,pose,[s])[1]['id']=='w'


def test_unknown_measurement_not_zero():
    m=measure(None);assert m['value'] is None;assert m['interval']['lower'] is None;assert m['status']=='unobserved'


def test_photo_adapter_excludes_sensor_folders(tmp_path):
    for name in ['room_1','lidar','depth','confidence']:
        d=tmp_path/name;d.mkdir();(d/'a.jpg').write_bytes(b'x');(d/'b.jpg').write_bytes(b'x')
    assert list(photo_groups(tmp_path))==['room_1']


def test_duplicate_truth_rejected(tmp_path):
    p=tmp_path/'truth.txt';p.write_text('room_1:\nheight: 2.8 m\nroom_1:\nheight: 2 m\n')
    with pytest.raises(ValueError,match='Duplicate'):read_measurements(p)


def test_staged_regions_do_not_trigger_concealed_damage():
    s={'id':'w','damage_ids':[]}
    d={'id':'d','surface_id':'w','status':'staged_marker_assessment','area':measure(.2,'m2')}
    scope,flags=scope_and_flags([d],[s]);assert not flags;assert scope[0]['action']=='inspect_staged_region_demo'


def test_gravity_recovers_tilt_without_scale_change():
    from scipy.spatial.transform import Rotation
    from astra.geometry import gravity_alignment
    rotation=Rotation.from_euler('x',20,degrees=True).as_matrix()
    normals=np.tile(np.array([0.,1.,0.])@rotation.T,(200,1))
    aligned=gravity_alignment(normals)
    np.testing.assert_allclose(normals[0]@aligned.T,[0,1,0],atol=1e-7)
    assert np.linalg.det(aligned)==pytest.approx(1.)


def test_paired_openings_recover_adjacency():
    from astra.pipeline import adjacency_from_openings
    surfaces=[{'id':'a','room_id':'one','start':[0,0],'end':[3,0]},
              {'id':'b','room_id':'two','start':[3,.15],'end':[0,.15]}]
    openings=[{'id':str(i),'surface_id':sid,'room_id':rid,'kind':'doorway',
               'surface_uv_bounds':[[1,0],[2,2.2]],'width':measure(1.)} for i,sid,rid in [(0,'a','one'),(1,'b','two')]]
    result=adjacency_from_openings({'surfaces':surfaces,'openings':openings})
    assert len(result)==1 and result[0]['rooms']==['one','two']
    openings[1]['kind']='window'
    assert adjacency_from_openings({'surfaces':surfaces,'openings':openings})==[]
