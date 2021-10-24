const int AA = 2;

const float pi = 3.14159;

const vec3 SKY_BASE_COLOR = vec3(0.9, 0.7, 1.0);

const float PI = 3.14159;

const float eps = 1e-4;

const mat3 identityTransform = mat3( 1.0, 0.0, 0.0, 
				 0.0, 1.0, 0.0, 
				 0.0, 0.0, 1.0);

// environment
const vec3 SUNLIGHT_DIR = vec3(0.4, 0.7, 0.1);

const vec3 X_AXIS = vec3(1.,0.,0.);
const vec3 Y_AXIS = vec3(0.,1.,0.);
const vec3 Z_AXIS = vec3(0.,0.,1.);

// Procedural 3d noise from Inigo Quilez at https://www.shadertoy.com/view/4sfGzS
float hash(in vec3 p)  // replace this by something better
{
    p  = fract( p*0.3183099+.1 );
	p *= 17.0;
    return fract( p.x*p.y*p.z*(p.x+p.y+p.z) );
}

// object ID definitions (DO NOT MODIFY)
const float SKY   = -1.;
const float PLANE = 1.;
const float TREE = 2.;

struct Params { 
    vec2  fragCoord;
    vec2  iResolution;               
	float time;       
};


// how to cast into the scene --- castRay returns a vec4 of <d, obj_id, uv>
struct Query {
    vec3 ro;
    vec3 rd;
};

// what gets returns from a uv/material query
struct Material {
   vec3  col;
   vec3  nor;
   float spec;
};

struct QueryResult {
    float d;
    float obj_id;
    vec3 uvw;
    //vec3 norm; 
};




// matrix math helper, ty inigo quilez
mat3 rotationAxisAngle( in vec3 v, in float angle )
{
    float s = sin( angle );
    float c = cos( angle );
    float ic = 1.0 - c;

    return mat3( v.x*v.x*ic + c,     v.y*v.x*ic - s*v.z, v.z*v.x*ic + s*v.y,
                 v.x*v.y*ic + s*v.z, v.y*v.y*ic + c,     v.z*v.y*ic - s*v.x,
                 v.x*v.z*ic - s*v.y, v.y*v.z*ic + s*v.x, v.z*v.z*ic + c);
}

mat3 rotate( in mat3 transform, in vec3 v, in float angle ) {
    mat3 forwards = rotationAxisAngle(v, angle);
    
    return forwards * transform;
}

// Compute camera-to-world transformation.
mat3 setCamera( in vec3 ro, in vec3 ta, in float cr )
{
	vec3 cw = normalize(ta - ro);
	vec3 cp = vec3(sin(cr), cos(cr),0.0);
	vec3 cu = normalize( cross(cw,cp) );
	vec3 cv = normalize( cross(cu,cw) );
    return mat3( cu, cv, cw );
}

// vec3(distance, material uv)
QueryResult sdPlane(in vec3 p, in float time )
{    
    float d  = return p.y;
    vec3 uvw  = p.xzy;
	return QueryResult(d, PLANE, uvw); // vec4(p.y, p.xyz) maybe?
}



float sdCapsule(in vec3 p, in vec3 a, in vec3 b, in float r)
{

    vec3 pa = p - a, ba = b - a;
    float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 );
    float d = length( pa - ba*h ) - r;
    //vec3 uvw = vec3(0.);
    //return QueryResult(d, TREE, uvw);
    return d;
}

// x, m, uv
QueryResult opS2(in QueryResult d1, in QueryResult d2 )
{
    float a = (d1.d > -d2.d) ? 1. : 0.;
    float b = 1. - a;

    float d      = a * d1.d  + b * -d2.d;
    float obj_id = a * d1.obj_id  + b * d2.obj_id;
    vec3 uvw     = a * d1.uvw + b * d2.uvw;

    return QueryResult(d, obj_id, uvw);
    //return (d1.d > -d2.d) ? d1 : Casting(-d2.d, d2.mat, d2.mat_aux);
    //max(d1.x, -d2.x)
}

// union primitives 1 and 2
// d1 is a vec2 where .x is the distance, and .y is the color/material code.
QueryResult opU2(in QueryResult d1, in QueryResult d2 )
{
    float a = (d1.d < d2.d) ? 1.0 : 0.0;
    float b = 1. - a;

    float d      = a * d1.d  + b * d2.d;
    float obj_id = a * d1.obj_id  + b * d2.obj_id;
    vec3 uvw     = a * d1.uvw + b * d2.uvw;

	//return (d1.d<d2.d) ? d1 : d2;
    return QueryResult(d, obj_id, uvw);
}

struct Segment {
    vec3 pos;
    mat3 orientation;
    float length;
    float width;
};



vec3 endOfSegment(in Segment segment) {
    return segment.pos + (segment.orientation * vec3(0.,segment.length,0.));
}

float sdSegment(in vec3 p, in Segment segment) {
    return sdCapsule(p, segment.pos, endOfSegment(segment), segment.width);
}



mat3 perturb(in mat3 transform, in vec3 seed, in float scale) {
    float randAngle1 = scale * 2. * PI * (hash((1.*seed))-0.5);
    float randAngle2 = scale * 2. * PI * (hash((2.*seed))-0.5);
    float randAngle3 = scale * 2. * PI * (hash((3.*seed))-0.5);
    return rotate(rotate(rotate(transform, X_AXIS, randAngle1), Y_AXIS, randAngle2), Z_AXIS, randAngle3);
}

float grow(in float t, in float startT, in float endT) {
    return clamp(t - startT, 0., endT - startT) / (endT-startT);
}


vec3 next(in vec3 start, mat3 angle, float length) {
    return start + length * (angle * Y_AXIS);
}

vec3 nextAngle(in mat3 angle, in vec3 seed) {
    perturb()
}


float sdTree(in vec3 p, in vec3 pos, in float scale, in float time) {

    //vec3 seed = floor(p.xxz / 2.);
    //vec3 pMod = vec3( mod(p.xz, 2.).xy, p.y).xzy;
    vec3 seed = pos;
    vec3 pMod = p;
    
    vec3 t000 = pos;
    vec3 t100 = next(pos, identityTransform, scale);

    /*
    float length1 = scale  * 0.5;
    float width1  = length1 * 0.2;
    mat3  angle1  = identityTransform;
    vec3  start1  = pos; //  + vec3(0.5,0.,0.5)*(hash(pos) - 0.5)
    
    
    float length2 = length1;
    float width2 = width1;
    mat3 angle2 = angle1;
    vec3 start2 = start1;

    float length3 = length1;
    float width3 = width1;
    mat3 angle3 = angle1;
    vec3 start3 = start1;

    */


    /*

    Segment segment1 = Segment(start1, angle1, scale, width1);
    Segment segment2 = segment1;
    
    float d = sdSegment(pMod, segment1);

    for (int i = 0; i < 5; i++) {
    
        length1  = length1 * 0.9;
        width1   = width1 * 0.9;
        angle1   = perturb(angle1, seed + vec3(float(i), 0., 0.),0.1);
        start1   = endOfSegment(segment1);

        segment1 = Segment(start1, angle1, length1, width1);
        d = min(d, sdSegment(pMod, segment1));
        
        length2 = length1 * 0.9;
        width2  = width1 * 0.9;
        angle2  = perturb(angle1, seed + vec3(float(i),1.,0.),0.25);
        start2 = start1;
        
        segment2 = segment1;
        
        for (int j = 0; j < 5; j++) {
        
            length2 = length2 * 0.9;
            width2  = width2 * 0.9;
            angle2  = perturb(angle2, seed + vec3(float(i),1.+float(j),0.), 0.1);
            start2  = endOfSegment(segment2);
            
            segment2 = Segment(start2, angle2, length2, width2);
            d = min(d, sdSegment(pMod, segment2));

        }
    }

    return d;
    */
    
    return d;
}

QueryResult map( in vec3 p, in Params params)
{

    // plane
    QueryResult scene = sdPlane(p, params.time);

    vec3 treePos = vec3(1., 0., 1.);

    QueryResult tree = QueryResult(sdTree( p, treePos, 0.6, params.time), TREE, vec3(1.));
    scene = opU2(scene, tree);

    return scene;
}


Query getQuery(in Params params)
{
    vec2 mo = iMouse.xy/iResolution.xy;
    vec2 p = (-params.iResolution.xy + 2.0*params.fragCoord)/params.iResolution.y;
    float time = params.time;
    
    // todo: move camera on right click, interact on left click: + CAMERA_MOUSE * 2. * mo.y
    //vec3 ro = vec3( 0.0, 1.0, -5.);
    vec3 ta = vec3( 0.0, 1.0, 0.0 );
    vec3 ro = ta + vec3( 4.5*cos(0.1*time + 7.0*mo.x), 1.3 + 2.0*mo.y, 4.5*sin(0.1*time + 7.0*mo.x) );

    // camera-to-world transformation
    mat3 ca = setCamera( ro, ta, 0.0 );
    // ray direction
    vec3 rd = ca * normalize( vec3(p.xy,2.0) );
    
    return Query(ro, rd);
}

// Cast a ray from origin ro in direction rd until it hits an object.
// Return (t,m,a) where t is distance traveled along the ray, and m
// is the material of the object hit, and a is an auxilliary material channel
QueryResult castRay( in Query query, in Params params)
{
    float tmin = 1.0;
    float tmax = 20.0;

    vec3 rd = query.rd;
    vec3 ro = query.ro;
   
    // bounding volume
    float tp1 = (-0.1-ro.y)/rd.y; if( tp1>0.0 ) tmax = min( tmax, tp1 );
    float tp2 = (10.6-ro.y)/rd.y; if( tp2>0.0 ) { if( ro.y>10.6 ) tmin = max( tmin, tp2 );
                                                 else           tmax = min( tmax, tp2 ); }
    
    float t = tmin;


    float obj_id = -1.0;
    vec3  uvw    = vec3(0.);

    for( int i=0; i<200; i++ )
    {
	    float precis = 0.0001*t;
	    QueryResult res = map( ro+rd*t, params);
        if( res.d<precis || t>tmax ) break;
        t += 0.9*res.d;
	    obj_id = res.obj_id;
        uvw = res.uvw;
    }

    if( t>tmax )
    {
        obj_id=SKY;
        uvw = vec3(0.,rd.y, 0.);
    }
    return QueryResult( t, obj_id, uvw);
}



// Cast a shadow ray from origin ro (an object surface) in direction rd
// to compute soft shadow in that direction. Returns a lower value
// (darker shadow) when there is more stuff nearby as we step along the shadow ray.
float softshadow( in vec3 ro, in vec3 rd, in float mint, in float tmax, in Params params)
{
	float res = 1.0;
    float t = mint;
    for( int i=0; i<16; i++ )
    {
		float h = map( ro + rd*t, params).d;
        res = min( res, 6.0*h/t );
        t += clamp( h, 0.02, 0.10 );
        if( h<0.001 || t>tmax ) break;
    }
    return clamp( res, 0.0, 1.0 );
}

// Compute normal vector to surface at pos, using central differences method?
vec3 calcNormal( in vec3 pos, in Params params)
{
    // epsilon = a small number
    vec2 e = vec2(1.0,-1.0)*0.5773*0.0005;
    
    return normalize( e.xyy*map( pos + e.xyy, params ).d + 
					  e.yyx*map( pos + e.yyx, params ).d + 
					  e.yxy*map( pos + e.yxy, params ).d + 
					  e.xxx*map( pos + e.xxx, params ).d );

}

// compute ambient occlusion value at given position/normal
float calcAO( in vec3 pos, in vec3 nor, in Params params)
{
	float occ = 0.0;
    float sca = 1.0;
    for( int i=0; i<5; i++ )
    {
        float hr = 0.01 + 0.12*float(i)/4.0;
        vec3 aopos =  nor * hr + pos;
        float dd = map( aopos, params).d;
        occ += -(dd-hr)*sca;
        sca *= 0.95;
    }
    return clamp( 1.0 - 3.0*occ, 0.0, 1.0 );    
}

vec3 Sky(in Params params, in vec3 uvw) {
    return clamp(SKY_BASE_COLOR + uvw.y*0.8, 0., 1.);
}

vec3 Tree(in Params params, in vec3 uvw) {
    return vec3(0.5);
}

// Interpret the material and uvw and produce info for final rendering
// todo: make this less branchy
Material mat_col(in Params params, in QueryResult queryResult)
{
    
    float x = queryResult.uvw.x;
    float y = queryResult.uvw.y;
    float obj_id = queryResult.obj_id;    
    
    vec3 nor = vec3(0.);
    float spec = 0.;
    
    // color
    vec3 sky          = Sky(params, queryResult.uvw);
    
    
    vec3 plane = 0.3 + 0.1*(mod( floor(5.0*x) + floor(5.0*y), 2.0))*vec3(1.0);
        
    vec3 tree = Tree(params, queryResult.uvw);
    
    vec3 col = 
               step(-obj_id, -1. * -1.5) * step(obj_id, -0.5)  * sky   +   // -1 -->  -1.5  < x  < -0.5
               step(-obj_id, -1. *  0.5) * step(obj_id, 1.5)   * plane +   //  1 -->   0.5  < x  <  1.5
               step(-obj_id, -1. *  1.5) * step(obj_id, 2.5)   * tree;     //  2 -->   1.5  < x  <  2.5
    
    
    return Material(col, nor, spec); 
}



// Render by fetching from the scene buffer and interpreting it to get diffuse
// TODO: Then, add in shadows, AO, etc.
vec3 render2(in vec2 fragCoord)
{

    Params params = Params(  fragCoord, iResolution.xy, iTime); // mod(iTime,10.)
    Query query = getQuery(params);
    QueryResult scene = castRay( query, params );

    // Get the scene info from the scene buffer
    //vec4 scene = texelFetch(iChannel1, ivec2(fragCoord), 0);
    
    // alias some stuff from the scene buffer
    float d      = scene.d;
    float obj_id = scene.obj_id;
    vec3  uvw    = scene.uvw;
    
    // form query based on current camera position, combine with depth to get scene position
    vec3 rd = query.rd;
    vec3 ro = query.ro;
    vec3 pos = d * rd + ro;
    
    /*vec3 mouseWorldPos     = getMouseWorldPos();
    if (length(pos - mouseWorldPos) < 0.25)
    {
        return vec3(1.);
    }*/
    
    
    // material info
    Material mat = mat_col(params, scene);
    
    
    vec3 col = mat.col;

    // if not the sky, apply effects.
    if (obj_id > 0.)
    {
        vec3 nor = calcNormal( pos, params );
        vec3 ref = reflect( rd, nor ); // reflected ray

        // lighting        
        float occ = calcAO( pos, nor, params ); // ambient occlusion
		vec3  lig = normalize( SUNLIGHT_DIR ); // sunlight
		float amb = clamp( 0.5+0.5*nor.y, 0.0, 1.0 ); // ambient light
        float dif = clamp( dot( nor, lig ), 0.0, 1.0 ); // diffuse reflection from sunlight
        // backlight
        float bac = clamp( dot( nor, normalize(vec3(-lig.x,0.0,-lig.z))), 0.0, 1.0 )*clamp( 1.0-pos.y,0.0,1.0);
        float dom = smoothstep( -0.1, 0.1, ref.y ); // dome light
        float fre = pow( clamp(1.0+dot(nor,rd),0.0,1.0), 2.0 ); // fresnel
		float spe = pow(clamp( dot( ref, lig ), 0.0, 1.0 ),16.0); // specular reflection
        
        dif *= softshadow( pos, lig, 0.02, 2.5, params );
        dom *= softshadow( pos, ref, 0.02, 2.5, params );

		vec3 lin = vec3(0.0);
        lin += (1.30)*dif*vec3(1.00,0.80,0.55);
		lin += (2.00 + mat.spec)*spe*vec3(1.00,0.90,0.70)*dif;
        lin += 0.40*amb*vec3(0.40,0.60,1.00)*occ;
        lin += 0.50*dom*vec3(0.40,0.60,1.00)*occ;
        lin += 0.50*bac*vec3(0.25,0.25,0.25)*occ;
        lin += 0.25*fre*vec3(1.00,1.00,1.00)*occ;
		col = col*lin;
        
        // mix in fog?
        vec3 fog_col = SKY_BASE_COLOR;
    	col = mix( col, fog_col, 1.0-exp( -0.0002*d*d*d ) );
    }
    
    return vec3( clamp(col,0.0,1.0) );
}


void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec3 tot = vec3(0.0);
    for( int m=0; m<AA; m++ )
    for( int n=0; n<AA; n++ )
    {
        // pixel coordinates
        vec2 o = vec2(float(m),float(n)) / float(AA) - 0.5;
        //vec2 p = (2.0*(fragCoord+o)-iResolution.xy)/iResolution.y;
        vec3 col = render2(fragCoord + o);

    
    
        tot += col;

    }
    tot /= float(AA*AA);


    fragColor = vec4(tot, 1.);
}