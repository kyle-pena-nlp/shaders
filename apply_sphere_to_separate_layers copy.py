from gimpfu import *
pdb = gimp.pdb
image = gimp.image_list()[0]
layers = image.layers[:-1]

i = 0
ang = 180.0/len(layers)
theta = 0.0
pdb.gimp_message("ang: {}".format(str(ang)))
for layer in (layers):
   theta += ang
   pdb.gimp_message(str(theta))
   gimp_Layer = layer
   pdb.plug_in_map_object(
        #image, drawable, maptype=sphere
        image,gimp_Layer,1,
        #viewpoint x, y, z
        0.5,0.5,1,
        #position x, y, z
        0.5,0.5,0,
        #first-axis x, y, z
        1.,0.,0.,
        #second-axis x, y, z
        0.,1.,0.,
        #rotation-angle x, y, z
        0.,theta,0.,
        #lighttype=none
        0,
        #light color (r,g,b)
        (255,255,255),
        #light position x, y, z
        3.3,-3.7,-2.5,
        #light direction x, y, z
        -1.,-1.,1.,
        #ambientintesity, diffuseintesity, dissufereflectivity, specularreflectivity
        0.3,1,0.5,0.5,
        #highlight, antialiasing, tiled, newimage, traparentbackground, radius
        27,1,1,0,1,0.25,
        #scale x, y, z
        0.5,0.5,0.5,
        #cylinderlegth, 8 drawables for cylinders & boxes
        0,gimp_Layer,gimp_Layer,gimp_Layer,gimp_Layer,gimp_Layer,gimp_Layer,gimp_Layer,gimp_Layer
   )