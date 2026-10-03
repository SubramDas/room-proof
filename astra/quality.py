"""Observable layout checks; an empty adjacency graph is never declared correct."""
import cv2,numpy as np
from .layout import measure


def topology_quality(rooms,adjacency,tier,physical_stitch=True):
    if not rooms:return {'status':'unresolved','room_overlaps':[],'connected_components':0,'footprint_area':measure(None,'m2')}
    polygons=[np.array(r['polygon']) for r in rooms];points=np.concatenate(polygons);origin=points.min(0)-.05;span=points.max(0)-origin+.05
    cell=max(.02,float(span.max()/1800));size=np.ceil(span/cell).astype(int)+2
    occupancy=np.zeros((size[1],size[0]),np.uint16);masks=[];overlaps=[]
    for r,poly in zip(rooms,polygons):
        mask=np.zeros(occupancy.shape,np.uint8);cv2.fillPoly(mask,[np.rint((poly-origin)/cell).astype(np.int32)],1)
        for other,previous in masks:
            other_poly=np.asarray(other['polygon'],np.float32);current_poly=np.asarray(poly,np.float32)
            if cv2.isContourConvex(other_poly) and cv2.isContourConvex(current_poly):
                area=float(cv2.intersectConvexConvex(other_poly,current_poly)[0])
            else:
                interior=cv2.erode(mask,np.ones((3,3),np.uint8));previous_interior=cv2.erode(previous,np.ones((3,3),np.uint8))
                area=float(np.sum((interior>0)&(previous_interior>0))*cell*cell)
            # Exact convex intersections, or an interior raster for concave fallback.

            if area>max(.025,.01*min(r['floor_area']['value'],other['floor_area']['value'])):
                overlaps.append({'rooms':[other['id'],r['id']],'overlap_m2':area})
        masks.append((r,mask));occupancy+=mask
    ids={r['id'] for r in rooms};graph={i:set() for i in ids}
    for edge in adjacency:
        a,b=edge['rooms']
        if a in graph and b in graph:graph[a].add(b);graph[b].add(a)
    unseen=set(ids);components=[]
    while unseen:
        todo=[unseen.pop()];component=[]
        while todo:
            n=todo.pop();component.append(n)
            for q in graph[n]&unseen:unseen.remove(q);todo.append(q)
        components.append(sorted(component))
    area=float(np.sum(occupancy>0)*cell*cell)
    valid=physical_stitch and not overlaps and len(components)==1
    return {'status':'provisional_connected_layout' if valid else 'unresolved_physical_stitch','physical_coordinates_observed':physical_stitch,
        'room_overlaps':overlaps,'connected_components':len(components),'components':components,
        'footprint_area':measure(area,'m2',half_width=area*(.1 if tier=='lidar' else .6),method='raster_union_of_inferred_rooms'),
        'raster_resolution_m':cell,'warning':'Connectivity is inferred evidence, not externally verified correctness; area intervals are uncalibrated.'}
