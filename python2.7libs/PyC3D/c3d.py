import hou, math, os
from PyC3D import import_c3d

def find_height(fileData):
	"""
		Heuristic to find the height of the subject in the markerset
		(only works for standing poses)
	"""
	zmin = None
	hidx = 2
	for ml in fileData.markerLabels:
		if 'LTOE' in ml:
			hd = ml.replace('LTOE', 'LFHD')
			if hd not in fileData.markerLabels:
				break
			pmin_idx = fileData.markerLabels.index(ml)
			pmax_idx = fileData.markerLabels.index(hd)
			zmin = fileData.frames[0][pmin_idx].position[hidx]
			zmax = fileData.frames[0][pmax_idx].position[hidx]
	if zmin is None:  # could not find named markers, get extremes
		allz = [m.position[hidx] for m in fileData.frames[0]]
		zmin, zmax = min(allz), max(allz)
	return abs(zmax - zmin)

def adjust_scale_magnitude(height, scale):
	mag = math.log10(height * scale)
	#print('mag',mag, 'scale',scale)
	return scale * math.pow(10, -int(mag))

def adjust_scale(height, scale):
	factor = height * scale / 1.75  # normalize
	if factor < 0.5:
		scale /= 10.0
		factor *= 10.0
	cmu_factors = [(1.0, 1.0), (1.1, 1.45), (1.6, 1.6), (2.54, 2.54)]
	sqerr, fix = min(((cf[0] - factor) ** 2.0, 1.0 / cf[1])
		for cf in cmu_factors)
	#print('height * scale: {:.2f}'.format(height * scale))
	#print(factor, fix)
	return scale * fix


def writeCLIP(fileData, chanf, meta, scale):

	if chanf: clip_path = chanf + "/" + os.path.split(fileData.fileName)[1].replace(".c3d", ".clip")
	else: clip_path = fileData.fileName.replace(".c3d", ".clip")
	f = open(clip_path, "wb")
	try:
	# Write houdini DAE-clip data
		try:
			f.write('{\n')
			f.write("\trate = %d\n" % (meta[2]))
			f.write("\tstart = %d\n" % (meta[0]))
			f.write("\ttracklength = %d\n" % (meta[1]))
			f.write("\ttracks = %d\n" % (meta[3]*3+meta[3]))

			cords = ["tx","ty","tz"]
			scmult = hou.hmath.buildScale(scale, scale, scale)
			rot = hou.hmath.buildRotate(-90, 0, 0)
			iter = 0
			for _cr in cords:
				for tr in xrange(meta[3]):
					name =  _cr + str(tr)
					f.write("\t{\n")
					f.write("\t\tname = %s\n" % (name))
					_pt_cont = []
					for fr in range(meta[0], meta[1]):
							m = fileData.getMarker(fileData.markerLabels[tr],fr)
							p = m.position
							k = hou.Vector3(p)*scmult*rot
							_pt_cont.append(k[iter])
					data = " ".join(map(str, _pt_cont))
					f.write("\t\tdata = %s\n" % (data))
					f.write('\t}\n')
				iter=iter+1

			for ml in fileData.markerLabels:
				temp_m = str(ml.replace(":","_"))
				iter = 0
				f.write("\t{\n")
				name =  temp_m
				f.write("\t\tname = %s\n" % (name))
				_pt_cont = []
				for fr in range(meta[0], meta[1]):
					p = [0,0,0]
					_pt_cont.append(p[iter])
				data = " ".join(map(str, _pt_cont))
				f.write("\t\tdata = %s\n" % (data))
				iter=iter+1
				f.write('\t}\n')
			f.write('}\n')
		finally:
			f.close()
	except IOError:
		pass
	return clip_path


def writeCLIP_LOC(fileData, chanf, meta, scale):
	try:
		if chanf: clippath = chanf + "/" + os.path.split(fileData.fileName)[1].replace(".c3d", "_loc.clip") 
		else: clippath = fileData.fileName.replace(".c3d", "_loc.clip")
		f = open(clippath, "wb")
		try:
			f.write('{\n')
			f.write("\trate = %d\n" % (meta[2]))
			f.write("\tstart = %d\n" % (meta[0]))
			f.write("\ttracklength = %d\n" % (meta[1]))
			f.write("\ttracks = %d\n" % (meta[3]*3))

	# Write markers position and names to .clip file

			cords = [":tx",":ty",":tz"]

			scmult = hou.hmath.buildScale(scale, scale, scale)
			rot = hou.hmath.buildRotate(-90, 0, 0)

			for ml in fileData.markerLabels:
				temp_m = str(ml.replace(":","_"))
				iter = 0
				for _cr in cords:
					f.write("\t{\n")
					name =  temp_m + _cr
					f.write("\t\tname = %s\n" % (name))
					_pt_cont = []
					for fr in range(meta[0], meta[1]):
						m = fileData.getMarker(ml,fr)
						p = m.position
						k = hou.Vector3(p)*scmult*rot
						_pt_cont.append(k[iter])
					data = " ".join(map(str, _pt_cont))
					f.write("\t\tdata = %s\n" % (data))
					iter=iter+1
					f.write('\t}\n')
			f.write('}\n')
		finally:
			f.close()
	except IOError:
		pass

def CreateMarkerSet(filePath, markerSetType=True, rate_on=False, rate=24, frame_on=False, f_start=1, f_end=100, chanf="", pscale = 1.0, auto_magnitude=True, auto_scale=False):
	try:
		fileData = import_c3d.read(filePath)

		startFrame = fileData.startFrame
		endFrame = fileData.endFrame
		frameRate = fileData.frameRate
		markerCount = fileData.markerCount
		meta = [startFrame, endFrame, frameRate, markerCount]

		#### Scale

		height = find_height(fileData)
		scale = 1.0
		scale *= fileData.scale
		if auto_magnitude:
			scale = adjust_scale_magnitude(height, scale)

		if auto_scale:
			scale = adjust_scale(height, scale)
		scale *= pscale

		#####

		tempMakers = fileData.markerLabels
		allMarkers = []

		for _marker in tempMakers:
			allMarkers.append(_marker.replace(":","_"))

		if markerSetType == False:
			
			writeCLIP(fileData, chanf, meta, scale)
			
			root = hou.node('obj').createNode('geo', 'C3D_Markers')
			root.children()[0].destroy()
			
			pointgen = root.createNode('pointgenerate', 'GenMarkers')
			pointgen.parm('npts').set(markerCount)
			
			atrcrt = root.createNode('attribcreate', 'AddNames')
			atrcrt.setInput(0,pointgen)
			atrcrt.parm('name1').set('marker_name')
			atrcrt.parm('type1').set(4)

			chanim = root.createNode('channel', 'ChopAnimation')
			chanim.setInput(0,atrcrt)
			chanim.parm('method').set(2)

			exp = "`pythonexprs('hou.node("+'"../motiondata/names"'+").tracks()[hou.pwd().curPoint().number()].name()')`"
			atrcrt.parm('string1').set(exp)
			
			chnet = root.createNode('chopnet', 'motiondata')
			rclip = chnet.createNode('file', 'read_clip')

			rclip.parm('rateoption').set(rate_on)
			rclip.parm('rate').set(rate)

			trueFPath = ""
			if chanf: trueFPath = str(chanf + "/" + os.path.split(fileData.fileName)[1].replace(".c3d", ".clip"))
			else: trueFPath = fileData.fileName.replace(".c3d", ".clip")
			


			rclip.parm('file').set(trueFPath)

			shift = chnet.createNode('shift', 'shift_clip')
			shift.parm('units').set(0)
			shift.parm('relative').set(0)
			shift.parm('start').set(f_start)


			trim = 	chnet.createNode('trim', 'trim_clip')
			trim.parm('relative').set(0)
			trim.parm('units').set(0)
			if frame_on == True:
				trim.bypass(0)
				shift.bypass(0)
			else:
				trim.bypass(1)
				shift.bypass(1)
			trim.parm('start').set(f_start)
			trim.parm('end').set(f_end)

			del_t = chnet.createNode('delete', 'delete_transform')
			nm = chnet.createNode('null', 'names')
			data_null = chnet.createNode('null', "data")
			
			shift.setInput(0,rclip)
			trim.setInput(0,shift)
			del_t.setInput(0,trim)
			nm.setInput(0,del_t)
			data_null.setInput(0,trim)

			chanim.setDisplayFlag(1)
			chanim.setRenderFlag(1)
			chanim.parm('choppath').set(data_null.path())

			## Layout Nodes
			for ps in hou.node("/obj/C3D_Markers").allSubChildren():
				ps.moveToGoodPosition()

		else:

			writeCLIP_LOC(fileData, chanf, meta, scale)

			root = hou.node('obj').createNode('null', 'C3D_Root')
			subn = hou.node("obj").createNode("subnet", "markers")
			subnInputs = subn.indirectInputs()
			subn.setInput(0,root)
			chnet = subn.createNode('chopnet', 'motiondata')
			rclip = chnet.createNode('file', 'read_clip')
			rclip.parm('rateoption').set(rate_on)
			rclip.parm('rate').set(rate)

			trueFPath = ''
			if chanf: trueFPath = str(chanf + "/" + os.path.split(fileData.fileName)[1].replace(".c3d", "_loc.clip"))
			else: trueFPath = fileData.fileName.replace(".c3d", "_loc.clip")

			rclip.parm('file').set(trueFPath)

			shift = chnet.createNode('shift', 'shift_clip')
			shift.parm('units').set(0)
			shift.parm('relative').set(0)
			shift.parm('start').set(f_start)


			trim = 	chnet.createNode('trim', 'trim_clip')
			trim.parm('relative').set(0)
			trim.parm('units').set(0)
			if frame_on == True:
				trim.bypass(0)
				shift.bypass(0)
			else:
				trim.bypass(1)
				shift.bypass(1)
			trim.parm('start').set(f_start)
			trim.parm('end').set(f_end)

			shift.setInput(0,rclip)
			trim.setInput(0,shift)

			data_null = chnet.createNode('null', "data")
			data_null.setInput(0,trim)

			for _marker in allMarkers:
				tmp_marker = subn.createNode('null', str(_marker))
				tmp_marker.setInput(0,subnInputs[0])
				t_idx = ["tx", "ty", "tz"]
				for idx in t_idx:
					exp = 'chop("../motiondata/data/" + $OS + ":'+idx+'")'
					tmp_marker.parm(idx).setExpression(exp)
					tmp_marker.parm('geoscale').set(0.1)

			## Layout Nodes
			for ps in hou.node("/obj").allSubChildren():
				ps.moveToGoodPosition()

	except IOError:
		pass




# openpath = hou.expandString(hou.ui.selectFile())
# print openpath
# if openpath.find(".c3d") != -1 or openpath.find(".C3D") != -1:
# 	CreateMarkerSet(openpath)
# else: hou.ui.displayMessage('Wrong file Type selected, select C3D')