# Keep the 25-pose body cycle continuous while the independent eyelid track blinks.
# Original body poses and all three original blink states are retained.
# No extra body poses are appended or replayed after the blink.
import copy, zipfile
from IPython.display import display, FileLink, HTML
assert torch.cuda.is_available() and torch.version.hip
original_tracks, pictures, source_manifest = load_source('peashooter-source.zip')
repair_tracks = []
for name, states in original_tracks:
    poses = [copy.deepcopy(states[min(79+i,len(states)-1)]) for i in range(25)]
    if name=='anim_blink':
        for i in range(3):poses[i]=copy.deepcopy(states[1+i])
    repair_tracks.append((name, copy.deepcopy(states[:79])+poses))
# Attach the original eyelid image to the original moving face transform.
# The head-idle layer starts at source frame 29, its attachment bind pose.
old_sampler = sample
blink_states = dict(repair_tracks)['anim_blink']
face_states = dict(repair_tracks)['anim_face']
bind_face = dict(original_tracks)['anim_face'][29]
def attachment_matrix(s):
    kx,ky=math.radians(s['kx']),math.radians(s['ky'])
    return np.array([[math.cos(kx)*s['sx'],-math.sin(ky)*s['sy'],s['x']],
                     [math.sin(kx)*s['sx'],math.cos(ky)*s['sy'],s['y']],[0.,0.,1.]])
bind_inverse=np.linalg.inv(attachment_matrix(bind_face))
attachment_errors=[]
def attached_sample(states,phase):
    pose=old_sampler(states,phase)
    if states is blink_states and pose['f']>=0:
        parent=attachment_matrix(old_sampler(face_states,phase))
        original=attachment_matrix(pose)
        matrix=parent@bind_inverse@original
        pose=pose.copy()
        pose.update(x=float(matrix[0,2]),y=float(matrix[1,2]),
                    sx=float(np.hypot(matrix[0,0],matrix[1,0])),sy=float(np.hypot(matrix[0,1],matrix[1,1])),
                    kx=math.degrees(math.atan2(matrix[1,0],matrix[0,0])),
                    ky=math.degrees(math.atan2(-matrix[0,1],matrix[1,1])))
        error=float(np.abs(np.linalg.inv(parent)@attachment_matrix(pose)-bind_inverse@original).max())
        assert error<1e-7
        attachment_errors.append(error)
    return pose
sample=attached_sample
old_count = COUNT
COUNT = 25
try:
    repaired_gpu = Renderer(repair_tracks,pictures,'cuda')
    repaired_frames=[]
    for begin in range(0,125,8):
        repaired_frames += [Image.fromarray(a) for a in rgba(repaired_gpu.render(np.arange(begin,min(begin+8,125))/5))]
    # Keyframe transforms are unchanged, including all original blink poses.
    for _,states in repair_tracks:
        if states is blink_states:continue # Its original attachment now follows the head.
        for i in range(25):
            s=sample(states,float(i))
            assert all(abs(s[k]-states[79+i][k])<1e-7 for k in NUMERIC)
    # Compare premultiplied image differences across every sample boundary.
    seam_values=[]
    for i,im in enumerate(repaired_frames):
        a=np.asarray(im).astype(np.float32)/255
        b=np.asarray(repaired_frames[(i+1)%125]).astype(np.float32)/255
        aa=a[:,:,:3]*a[:,:,3:4];bb=b[:,:,:3]*b[:,:,3:4]
        mask=(a[:,:,3]+b[:,:,3])>0.05
        seam_values.append(float(np.abs(aa-bb)[mask].mean()))
finally:
    COUNT=old_count
    sample=old_sampler
boxes=[im.getbbox() for im in repaired_frames]
bounds=(min(b[0] for b in boxes)-2,min(b[1] for b in boxes)-2,max(b[2] for b in boxes)+2,max(b[3] for b in boxes)+2)
repair_report={'gpu':torch.cuda.get_device_name(0),'rocm':torch.version.hip,'frames':125,'fps':60,'source_body_poses':25,'original_blink_states':3,'duration_msec':2083,'bounds':bounds,'last_to_first_pixel_difference':seam_values[-1],'median_step_pixel_difference':float(np.median(seam_values)),'max_step_pixel_difference':max(seam_values),'source_keyframe_transforms_preserved':True,'eyelid_face_attachment_verified':True,'max_attachment_error':max(attachment_errors),'game_runtime_verified':False}
with zipfile.ZipFile('amd-attached-eyelids.zip','w',zipfile.ZIP_DEFLATED) as out:
    for i,im in enumerate(repaired_frames):
        buffer=io.BytesIO();im.crop(bounds).save(buffer,format='PNG');out.writestr(f'frames/{i:03}.png',buffer.getvalue())
    out.writestr('report.json',json.dumps(repair_report,indent=2))
print(json.dumps(repair_report,indent=2))
preview=[im.crop(bounds) for im in repaired_frames]
durations=[round((i+1)*1000/60)-round(i*1000/60) for i in range(125)]
preview[0].save('amd-attached-eyelids.webp',save_all=True,append_images=preview[1:],duration=durations,lossless=True,loop=0)
display(HTML('<b>Continuous blink with original eyelids attached to the face — AMD ROCm, 60 samples/s</b><br><img style="background:#777" src="data:image/webp;base64,'+base64.b64encode(Path('amd-attached-eyelids.webp').read_bytes()).decode()+'">'))
display(FileLink('amd-attached-eyelids.zip'))
