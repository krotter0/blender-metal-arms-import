from ..common.reader import BinaryReader, CFSphere, CFColorRGB, CFVec2, CFVec3, CFMtx43A

class FDX8VB_Info:
    def __init__(self,
        nVtxBytes: int,
        unlit: bool,
        nNormalCount: int,
        nWeightCount: int,
        nColorCount: int,
        nTCCount: int,
        nOffsetPos: int,
        nOffsetWeight: int,
        nOffsetNorm: int,
        nOffsetColor: int,
        nOffsetTC: int
    ):
        self.nVtxBytes = nVtxBytes
        self.unlit = unlit
        self.nNormalCount = nNormalCount
        self.nWeightCount = nWeightCount
        self.nColorCount = nColorCount
        self.nTCCount = nTCCount
        self.nOffsetPos = nOffsetPos
        self.nOffsetWeight = nOffsetWeight
        self.nOffsetNorm = nOffsetNorm
        self.nOffsetColor = nOffsetColor
        self.nOffsetTC = nOffsetTC
    
FDX8VB_InfoTable = [
    FDX8VB_Info(
        nVtxBytes=36,
        unlit=False,
        nNormalCount=1,
        nWeightCount=0,
        nColorCount=1,
        nTCCount=1,
        nOffsetPos=0,
        nOffsetWeight=255,
        nOffsetNorm=12,
        nOffsetColor=24,
        nOffsetTC=28,
    ),
    FDX8VB_Info(
        nVtxBytes=44,
        unlit=False,
        nNormalCount=1,
        nWeightCount=0,
        nColorCount=1,
        nTCCount=2,
        nOffsetPos=0,
        nOffsetWeight=255,
        nOffsetNorm=12,
        nOffsetColor=24,
        nOffsetTC=28,
    ),
    FDX8VB_Info(
        nVtxBytes=48,
        unlit=False,
        nNormalCount=1,
        nWeightCount=3,
        nColorCount=1,
        nTCCount=1,
        nOffsetPos=0,
        nOffsetWeight=12,
        nOffsetNorm=24,
        nOffsetColor=36,
        nOffsetTC=40,
    ),
    FDX8VB_Info(
        nVtxBytes=56,
        unlit=False,
        nNormalCount=1,
        nWeightCount=3,
        nColorCount=1,
        nTCCount=2,
        nOffsetPos=0,
        nOffsetWeight=12,
        nOffsetNorm=24,
        nOffsetColor=36,
        nOffsetTC=40,
    ),
    FDX8VB_Info(
        nVtxBytes=40,
        unlit=True,
        nNormalCount=0,
        nWeightCount=0,
        nColorCount=2,
        nTCCount=2,
        nOffsetPos=0,
        nOffsetWeight=255,
        nOffsetNorm=255,
        nOffsetColor=16,
        nOffsetTC=24,
    ),
    FDX8VB_Info(
        nVtxBytes=16,
        unlit=False,
        nNormalCount=0,
        nWeightCount=0,
        nColorCount=1,
        nTCCount=0,
        nOffsetPos=0,
        nOffsetWeight=255,
        nOffsetNorm=255,
        nOffsetColor=12,
        nOffsetTC=255,
    ),
    FDX8VB_Info(
        nVtxBytes=24,
        unlit=False,
        nNormalCount=0,
        nWeightCount=0,
        nColorCount=1,
        nTCCount=1,
        nOffsetPos=0,
        nOffsetWeight=255,
        nOffsetNorm=255,
        nOffsetColor=12,
        nOffsetTC=16,
    )
]

class FMeshSeg_t:
    def __init__(self):
        self.boundSphereMS = CFSphere()

    def read(self, reader: BinaryReader):
        self.boundSphereMS.read(reader)
        self.boneMtxCount = reader.read_U8()
        self.boneMtxIndexes = reader.read_U8s(4)
        if self.boneMtxCount > 1:
            raise NotImplementedError("Only segments with 0-1 bones are supported for now")

class FDX8BasisVectors_t:
    def __init__(self):
        self.fTx = 0.0
        self.fTy = 0.0
        self.fTz = 0.0
        self.fBx = 0.0
        self.fBy = 0.0
        self.fBz = 0.0

    def read(self, reader: BinaryReader):
        self.fTx = reader.read_F32()
        self.fTy = reader.read_F32()
        self.fTz = reader.read_F32()
        
        self.fBx = reader.read_F32()
        self.fBy = reader.read_F32()
        self.fBz = reader.read_F32()

class FDX8VB_t:
    def __init__(self):
        self.Link = FLink_t()

    def read(self, reader: BinaryReader):
        self.Link.read(reader)
        self.nVtxCount = reader.read_U32()
        self.nBytesPerVertex = reader.read_U16()
        if self.nBytesPerVertex % 4 != 0:
            raise NotImplementedError("Don't know how to treat nBytesPerVertex value of {}".format(self.nBytesPerVertex))
        
        self.nLMTCCount = reader.read_U16()
        self.pLMUVStream = reader.read_U32()
        self.basis = [FDX8BasisVectors_t() for _ in range(self.nVtxCount)]
        reader.read_ptr_objects(self.basis)
        
        nInfoIndex = reader.read_S8()
        self.info = FDX8VB_InfoTable[nInfoIndex]
        self.bDynamic = reader.read_BOOL8()
        self.bSoftwareVP = reader.read_BOOL8()
        
        self.bLocked = reader.read_BOOL8()
        self.pLockBuf = reader.read_U32()
        
        self.nLockOffset = reader.read_U32()
        self.nLockBytes = reader.read_U32()
        
        self.hVertexShader = reader.read_U32()
        
        pDXVB = reader.read_U32()
        
        lastPos = reader.tell()
        
        reader.seek(pDXVB)
        self.vb = []
        for i in range(self.nVtxCount):
            self.vb.append(reader.read_F32s(round(self.nBytesPerVertex / 4)))
        
        reader.seek(lastPos)

class FLink_t:
    def __init__(self):
        self.pPrevLink = 0
        self.pNextLink = 0

    def read(self, reader: BinaryReader):
        self.pPrevLink = reader.read_U32()
        self.pNextLink = reader.read_U32()

class FMeshTexLayerID_t:
    def __init__(self):
        self.m_ScrollSTPerSec = CFVec2()

    def read(self, reader: BinaryReader):
        self.nTexLayerID = reader.read_U8()
        self.nFlags = reader.read_U8()
        
        self.nFlipPageCount = reader.read_U8()
        self.nFramesPerFlip = reader.read_U8()
        
        self.apFlipPalette = reader.read_U32()
        
        reader.read_ptr_object(self.m_ScrollSTPerSec)
        
        self.m_fUVDegreeRotationPerSec = reader.read_F32()
        
        self.m_nCompressedUVRotAnchor = reader.read_U8s(2)
        reader.read_U8s(2) #PAD

class FMeshSkeleton_t:
    def read(self, reader: BinaryReader):
        self.parentBoneIndex = reader.read_U8()
        self.childBoneCount = reader.read_U8()
        self.childArrayStartIndex = reader.read_U8()

class FMeshBone_t:
    def __init__(self):
        self.AtRestBoneToModelMtx = CFMtx43A()
        self.AtRestModelToBoneMtx = CFMtx43A()
        self.AtRestParentToBoneMtx = CFMtx43A()
        self.AtRestBoneToParentMtx = CFMtx43A()
        
        self.SegmentedBoundSphere_BS = CFSphere()
        self.Skeleton = FMeshSkeleton_t()
        
    def read(self, reader: BinaryReader):
        self.name = reader.read_string(32)
        
        self.AtRestBoneToModelMtx.read(reader)
        self.AtRestModelToBoneMtx.read(reader)
        self.AtRestParentToBoneMtx.read(reader)
        self.AtRestBoneToParentMtx.read(reader)
        
        self.SegmentedBoundSphere_BS.read(reader)
        self.Skeleton.read(reader)
        
        self.flags = reader.read_U8()
        self.partID = reader.read_U8()
        reader.read_U8s(3) #PAD
        
class FShTexInst_t:
    def read(self, reader: BinaryReader):
        reader.skip(0x18) #CFTexInst
        self.nTextureNameOffset = reader.read_U16()
        self.nTexLayerID = reader.read_U8()
        reader.skip(0x1) #PAD

class FMeshMaterial_t:
    def __init__(self):
        self.materialTint = CFColorRGB()
        self.averageVertPos = CFVec3()
        self.platformData = FDX8MeshMaterial_t()

    def read(self, reader: BinaryReader):
        self.shLightRegisters = reader.read_U32()
        shSurfaceRegisters = reader.read_U32() #This contains multiple register pointers based on the surface shader used. First one is always textures

        self.lightShaderIdx = reader.read_U8()
        self.specularShaderIdx = reader.read_U8()
        self.surfaceShaderIdx = reader.read_U16()
        
        self.partIDMask = reader.read_U32()
        
        reader.read_ptr_object(self.platformData)
        #self.platformData = reader.readU32()
        #self.platformData.read(reader)
        
        self.lodMask = reader.read_U8()
        self.depthBiasLevel = reader.read_U8()
        self.baseSTSets = reader.read_U8()
        self.lightMapSTSets = reader.read_U8()
        self.texLayerIDIndex = reader.read_U8s(4)
        self.affectAngle = reader.read_F32()
        
        self.compAffectNormal = reader.read_S8s(3)
        self.affectBoneID = reader.read_S8()
        
        self.compressedRadius = reader.read_U8()
        
        reader.read_U8() #pad
        
        self.mtlFlags = reader.read_U16()
        self.drawKey = reader.read_U32()
        
        self.materialTint.read(reader)
        self.averageVertPos.read(reader)
        
        self.dlHashKey = reader.read_U32() #missing from old versions?
        
        #read textures
        with reader.detour(shSurfaceRegisters):
            textureRegister = reader.read_U32()
            reader.seek(textureRegister)
            shTextureInst = FShTexInst_t()
            shTextureInst.read(reader)
            
            reader.seek(shTextureInst.nTextureNameOffset)
            self.textureName = reader.read_string()

class FDX8MeshTriList_t:
    def read(self, reader: BinaryReader):
        self.nTriCount = reader.read_U16()
        self.nStartVindex = reader.read_U16()
        self.nVtxIndexMin = reader.read_U16()
        self.nVtxIndexRange = reader.read_U16()
        
class FDX8MeshStrip_t:
    def read(self, reader: BinaryReader):
        self.nTriCount = reader.read_U8()
        reader.read_U8() #__PAD
        self.nStartVindex = reader.read_U16()
        self.nVtxIndexMin = reader.read_U16()
        self.nVtxIndexRange = reader.read_U16()
        
class FDX8MeshCluster_t:
    def __init__(self):
        self.TriList = FDX8MeshTriList_t()
        
    def read(self, reader: BinaryReader):
        self.nStripCount = reader.read_U16()
        self.nFlags = reader.read_U8()
        self.nSegmentIdx = reader.read_U8()
        self.nVBIndex = reader.read_U8()
        self.nIBIndex = reader.read_U8()
        self.nPartID = reader.read_U8()
        self.nLODID = reader.read_U8()
        
        self.pPushBuffer = reader.read_U32() #missing from old models?
        self.TriList.read(reader)
        paStripBuffer = reader.read_U32()
        
        oldPos = reader.tell()
        reader.seek(paStripBuffer)
        
        self.StripBuffers = []
        for i in range(self.nStripCount):
            v = FDX8MeshStrip_t()
            self.StripBuffers.append(v)
            v.read(reader)
        
        reader.seek(oldPos)

class FDX8MeshMaterial_t:
    def __init__(self):
        pass
        
    def read(self, reader: BinaryReader):
        aCluster = reader.read_U32()
        nClusterCount = reader.read_U32()
        
        oldPos = reader.tell()
        
        reader.seek(aCluster)
        self.clusters = []
        for i in range(nClusterCount):
            v = FDX8MeshCluster_t()
            self.clusters.append(v)
            v.read(reader)
        
        reader.seek(oldPos)

class FDX8Mesh_s:
    def __init__(self):
        self.atRestBoundSphereMS = CFSphere()
        
    def read(self, reader: BinaryReader):
        self.flags = reader.read_U16()
        self.vbCount = reader.read_U8()
        self.ibCount = reader.read_U8()
        self.disposableOffset = reader.read_U32()
        
        self.atRestBoundSphereMS.read(reader)
        
        self.mesh = reader.read_U32()
        
        self.vb = [FDX8VB_t() for _ in range(self.vbCount)]
        reader.read_ptr_objects(self.vb)
        self.collVertBuffer = reader.read_U32()
        indicesCountsPointer = reader.read_U32()
        
        dxibs = reader.read_U32()
        
        oldPos = reader.tell()
        reader.seek(indicesCountsPointer)
        indiciesCounts = reader.read_U16s(self.ibCount)
        
        reader.seek(dxibs)
        
        indiciesPointers = reader.read_U32s(self.ibCount)
        self.indicies = []
        for i,p in enumerate(indiciesPointers):
            reader.seek(p)
            self.indicies.append(reader.read_U16s(indiciesCounts[i]))
        reader.seek(oldPos)

class Ape:
    def __init__(self):
        self.name = ""
        self.boundSphereMS = CFSphere()
        self.boundBoxMinMS = CFVec3()
        self.boundBoxMaxMS = CFVec3()
        
        self.meshIS = FDX8Mesh_s()
        
    def read(self, reader: BinaryReader):
        self.name = reader.read_string(16)
        self.boundSphereMS.read(reader)
        self.boundBoxMinMS.read(reader)
        self.boundBoxMaxMS.read(reader)
        self.flags = reader.read_U16()
        self.meshCollMask = reader.read_U16()
        self.usedBoneCount = reader.read_U8()
        self.rootBoneIndex = reader.read_U8()
        self.boneCount = reader.read_U8()
        self.segCount = reader.read_U8()
        self.texLayerIDCount = reader.read_U8()
        self.texLayerIDCount_ST = reader.read_U8()
        self.texLayerIDCount_Flip = reader.read_U8()
        self.lightCount = reader.read_U8()
        self.materialCount = reader.read_U8()
        self.collTreeCount = reader.read_U8()
        self.lodCount = reader.read_U8()
        self.shadowLODBias = reader.read_U8()
        
        self.lodDistances = reader.read_F32s(8)
        
        self.seg = [FMeshSeg_t() for _ in range(self.segCount)]
        reader.read_ptr_objects(self.seg, 24)
        
        self.boneArray = [FMeshBone_t() for _ in range(self.boneCount)]
        reader.read_ptr_objects(self.boneArray, 320)
        
        self.lightArray = reader.read_U32()
        
        skeletonIndexArrayPointer = reader.read_U32()
        oldPos = reader.tell()
        reader.seek(skeletonIndexArrayPointer)
        self.skeletonIndexArray = reader.read_U8s(self.boneCount)
        reader.seek(oldPos)
        
        self.mtl = [FMeshMaterial_t() for _ in range(self.materialCount)]
        reader.read_ptr_objects(self.mtl)
        
        self.collTree = reader.read_U32()
        
        #self.texLayerIDArray = [FMeshTexLayerID_t() for _ in range(self.texLayerIDCount)]
        #reader.readPtrObjects(self.texLayerIDArray)
        self.texLayerIDArray = reader.read_U32()
        
        reader.read_ptr_object(self.meshIS)