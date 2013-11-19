''' -- imports from python libraries -- '''
import hashlib # for calculating md5
# import os -- Keep such imports here


''' -- imports from installed packages -- '''
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.shortcuts import render_to_response, render
from django.template import RequestContext

from django_mongokit import get_database

try:
    from bson import ObjectId
except ImportError:  # old pymongo
    from pymongo.objectid import ObjectId

import magic  #for this install python-magic example:pip install python-magic
from PIL import Image #install PIL example:pip install PIL
from StringIO import StringIO


#from string import maketrans 


''' -- imports from application folders/files -- '''
from gnowsys_ndf.ndf.models import File

###########################################################################

def submitDoc(request):
    if request.method=="POST":
        title = request.POST.get("docTitle","")
        userid = request.POST.get("user","")
	print "userid",userid
        memberOf = request.POST.get("memberOf","")
	for each in request.FILES.getlist("doc[]",""):
		checkmd5=save_file(each,title,userid,memberOf)
                if (checkmd5=="True"):
                    return HttpResponse("File alreaday uploaded")
                else:
                    return HttpResponseRedirect("/ndf/documentList/")

def save_file(files,title,userid,memberOf):
	db=get_database()[File.collection_name]
	fileobj=db.File()
	filemd5= hashlib.md5(files.read()).hexdigest()
        files.seek(0)
        filetype=magic.from_buffer(files.read()) #Gusing filetype by python-magic
        print "filetype1:",filetype
	if fileobj.fs.files.exists({"md5":filemd5}):
		return "True"
	else:
		fileobj.name=unicode(title)
        	fileobj.created_by=int(userid)
        	fileobj.member_of=unicode(memberOf)
                fileobj.mime_type=filetype
        	fileobj.save()
		#mime = magic.Magic(mime=True)
		files.seek(0)  #moving files cursor to start
		filename=files.name
		#this code is for storing Document in gridfs
		objectid=fileobj.fs.files.put(files.read(),filename=filename,content_type=filetype)
		fileobj.fs_file_ids.append(objectid)
                #storing thumbnail of image in saved object
                if 'image' in filetype:
                    thumbnailimg=convert_image_thumbnail(files)
                    tobjectid=fileobj.fs.files.put(thumbnailimg,filename=filename+"-thumbnail",content_type=filetype)
                    fileobj.fs_file_ids.append(tobjectid)
		fileobj.save()
                print "filetype:",filetype
                return "False"

def convert_image_thumbnail(files):
    files.seek(0)
    thumb_io=StringIO()
    size=128,128
    img=Image.open(StringIO(files.read()))
    img.thumbnail(size,Image.ANTIALIAS)
    img.save(thumb_io,"JPEG")
    thumb_io.seek(0)
    return thumb_io
		

	
def GetDoc(request):
    filecollection=get_database()[File.collection_name]
    files=filecollection.File.find()
    template="ndf/DocumentList.html"
    variable=RequestContext(request,{'filecollection':files})
    return render_to_response(template,variable)

def readDoc(request,_id):
    filecollection=get_database()[File.collection_name]
    fileobj=filecollection.File.one({"_id": ObjectId(_id)})  
    fl=fileobj.fs.files.get(ObjectId(fileobj.fs_file_ids[0]))
    if 'image' in fl.content_type:
        fl=fileobj.fs.files.get(ObjectId(fileobj.fs_file_ids[1]))
    return HttpResponse(fl.read(),content_type=fl.content_type)
