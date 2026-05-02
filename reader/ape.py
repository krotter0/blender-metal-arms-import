from .common import BinaryReader, CFSphere, CFColorRGB, CFVec2, CFVec3, CFMtx43A

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
        self.boneMtxCount = reader.readU8()
        self.boneMtxIndexes = reader.readU8s(4)
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
        self.fTx = reader.readF32()
        self.fTy = reader.readF32()
        self.fTz = reader.readF32()
        
        self.fBx = reader.readF32()
        self.fBy = reader.readF32()
        self.fBz = reader.readF32()

class FDX8VB_t:
    def __init__(self):
        self.Link = FLink_t()

    def read(self, reader: BinaryReader):
        self.Link.read(reader)
        self.nVtxCount = reader.readU32()
        self.nBytesPerVertex = reader.readU16()
        if self.nBytesPerVertex % 4 != 0:
            raise NotImplementedError("Don't know how to treat nBytesPerVertex value of {}".format(self.nBytesPerVertex))
        
        self.nLMTCCount = reader.readU16()
        self.pLMUVStream = reader.readU32()
        self.basis = [FDX8BasisVectors_t() for _ in range(self.nVtxCount)]
        reader.readPtrObjects(self.basis)
        
        nInfoIndex = reader.readS8()
        self.info = FDX8VB_InfoTable[nInfoIndex]
        self.bDynamic = reader.readBOOL8()
        self.bSoftwareVP = reader.readBOOL8()
        
        self.bLocked = reader.readBOOL8()
        self.pLockBuf = reader.readU32()
        
        self.nLockOffset = reader.readU32()
        self.nLockBytes = reader.readU32()
        
        self.hVertexShader = reader.readU32()
        
        pDXVB = reader.readU32()
        
        lastPos = reader.tell()
        
        reader.seek(pDXVB)
        self.vb = []
        for i in range(self.nVtxCount):
            self.vb.append(reader.readF32s(round(self.nBytesPerVertex / 4)))
        
        reader.seek(lastPos)

class FLink_t:
    def __init__(self):
        self.pPrevLink = 0
        self.pNextLink = 0

    def read(self, reader: BinaryReader):
        self.pPrevLink = reader.readU32()
        self.pNextLink = reader.readU32()

class FMeshTexLayerID_t:
    def __init__(self):
        self.m_ScrollSTPerSec = CFVec2()

    def read(self, reader: BinaryReader):
        self.nTexLayerID = reader.readU8()
        self.nFlags = reader.readU8()
        
        self.nFlipPageCount = reader.readU8()
        self.nFramesPerFlip = reader.readU8()
        
        self.apFlipPalette = reader.readU32()
        
        reader.readPtrObject(self.m_ScrollSTPerSec)
        
        self.m_fUVDegreeRotationPerSec = reader.readF32()
        
        self.m_nCompressedUVRotAnchor = reader.readU8s(2)
        reader.readU8s(2) #PAD

class FMeshSkeleton_t:
    def read(self, reader: BinaryReader):
        self.parentBoneIndex = reader.readU8()
        self.childBoneCount = reader.readU8()
        self.childArrayStartIndex = reader.readU8()

class FMeshBone_t:
    def __init__(self):
        self.AtRestBoneToModelMtx = CFMtx43A()
        self.AtRestModelToBoneMtx = CFMtx43A()
        self.AtRestParentToBoneMtx = CFMtx43A()
        self.AtRestBoneToParentMtx = CFMtx43A()
        
        self.SegmentedBoundSphere_BS = CFSphere()
        self.Skeleton = FMeshSkeleton_t()
        
    def read(self, reader: BinaryReader):
        self.name = reader.readString(32)
        
        self.AtRestBoneToModelMtx.read(reader)
        self.AtRestModelToBoneMtx.read(reader)
        self.AtRestParentToBoneMtx.read(reader)
        self.AtRestBoneToParentMtx.read(reader)
        
        self.SegmentedBoundSphere_BS.read(reader)
        self.Skeleton.read(reader)
        
        self.flags = reader.readU8()
        self.partID = reader.readU8()
        reader.readU8s(3) #PAD
        
class FShTexInst_t:
    def read(self, reader: BinaryReader):
        reader.skip(0x18) #CFTexInst
        self.nTextureNameOffset = reader.readU16()
        self.nTexLayerID = reader.readU8()
        reader.skip(0x1) #PAD

class FMeshMaterial_t:
    def __init__(self):
        self.materialTint = CFColorRGB()
        self.averageVertPos = CFVec3()
        self.platformData = FDX8MeshMaterial_t()

    def read(self, reader: BinaryReader):
        self.shLightRegisters = reader.readU32()
        shSurfaceRegisters = reader.readU32() #This contains multiple register pointers based on the surface shader used. First one is always textures

        self.lightShaderIdx = reader.readU8()
        self.specularShaderIdx = reader.readU8()
        self.surfaceShaderIdx = reader.readU16()
        
        self.partIDMask = reader.readU32()
        
        reader.readPtrObject(self.platformData)
        #self.platformData = reader.readU32()
        #self.platformData.read(reader)
        
        self.lodMask = reader.readU8()
        self.depthBiasLevel = reader.readU8()
        self.baseSTSets = reader.readU8()
        self.lightMapSTSets = reader.readU8()
        self.texLayerIDIndex = reader.readU8s(4)
        self.affectAngle = reader.readF32()
        
        self.compAffectNormal = reader.readS8s(3)
        self.affectBoneID = reader.readS8()
        
        self.compressedRadius = reader.readU8()
        
        reader.readU8() #pad
        
        self.mtlFlags = reader.readU16()
        self.drawKey = reader.readU32()
        
        self.materialTint.read(reader)
        self.averageVertPos.read(reader)
        
        self.dlHashKey = reader.readU32() #missing from old versions?
        
        #read textures
        with reader.detour(shSurfaceRegisters):
            textureRegister = reader.readU32()
            reader.seek(textureRegister)
            shTextureInst = FShTexInst_t()
            shTextureInst.read(reader)
            
            reader.seek(shTextureInst.nTextureNameOffset)
            self.textureName = reader.readString()

class FDX8MeshTriList_t:
    def read(self, reader: BinaryReader):
        self.nTriCount = reader.readU16()
        self.nStartVindex = reader.readU16()
        self.nVtxIndexMin = reader.readU16()
        self.nVtxIndexRange = reader.readU16()
        
class FDX8MeshStrip_t:
    def read(self, reader: BinaryReader):
        self.nTriCount = reader.readU8()
        reader.readU8() #__PAD
        self.nStartVindex = reader.readU16()
        self.nVtxIndexMin = reader.readU16()
        self.nVtxIndexRange = reader.readU16()
        
class FDX8MeshCluster_t:
    def __init__(self):
        self.TriList = FDX8MeshTriList_t()
        
    def read(self, reader: BinaryReader):
        self.nStripCount = reader.readU16()
        self.nFlags = reader.readU8()
        self.nSegmentIdx = reader.readU8()
        self.nVBIndex = reader.readU8()
        self.nIBIndex = reader.readU8()
        self.nPartID = reader.readU8()
        self.nLODID = reader.readU8()
        
        self.pPushBuffer = reader.readU32() #missing from old models?
        self.TriList.read(reader)
        paStripBuffer = reader.readU32()
        
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
        aCluster = reader.readU32()
        nClusterCount = reader.readU32()
        
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
        self.flags = reader.readU16()
        self.vbCount = reader.readU8()
        self.ibCount = reader.readU8()
        self.disposableOffset = reader.readU32()
        
        self.atRestBoundSphereMS.read(reader)
        
        self.mesh = reader.readU32()
        
        self.vb = [FDX8VB_t() for _ in range(self.vbCount)]
        reader.readPtrObjects(self.vb)
        self.collVertBuffer = reader.readU32()
        indicesCountsPointer = reader.readU32()
        
        dxibs = reader.readU32()
        
        oldPos = reader.tell()
        reader.seek(indicesCountsPointer)
        indiciesCounts = reader.readU16s(self.ibCount)
        
        reader.seek(dxibs)
        
        indiciesPointers = reader.readU32s(self.ibCount)
        self.indicies = []
        for i,p in enumerate(indiciesPointers):
            reader.seek(p)
            self.indicies.append(reader.readU16s(indiciesCounts[i]))
        reader.seek(oldPos)

class Ape:
    def __init__(self):
        self.name = ""
        self.boundSphereMS = CFSphere()
        self.boundBoxMinMS = CFVec3()
        self.boundBoxMaxMS = CFVec3()
        
        self.meshIS = FDX8Mesh_s()
        
    def read(self, reader: BinaryReader):
        self.name = reader.readString(16)
        self.boundSphereMS.read(reader)
        self.boundBoxMinMS.read(reader)
        self.boundBoxMaxMS.read(reader)
        self.flags = reader.readU16()
        self.meshCollMask = reader.readU16()
        self.usedBoneCount = reader.readU8()
        self.rootBoneIndex = reader.readU8()
        self.boneCount = reader.readU8()
        self.segCount = reader.readU8()
        self.texLayerIDCount = reader.readU8()
        self.texLayerIDCount_ST = reader.readU8()
        self.texLayerIDCount_Flip = reader.readU8()
        self.lightCount = reader.readU8()
        self.materialCount = reader.readU8()
        self.collTreeCount = reader.readU8()
        self.lodCount = reader.readU8()
        self.shadowLODBias = reader.readU8()
        
        self.lodDistances = reader.readF32s(8)
        
        self.seg = [FMeshSeg_t() for _ in range(self.segCount)]
        reader.readPtrObjects(self.seg, 24)
        
        self.boneArray = [FMeshBone_t() for _ in range(self.boneCount)]
        reader.readPtrObjects(self.boneArray, 320)
        
        self.lightArray = reader.readU32()
        
        skeletonIndexArrayPointer = reader.readU32()
        oldPos = reader.tell()
        reader.seek(skeletonIndexArrayPointer)
        self.skeletonIndexArray = reader.readU8s(self.boneCount)
        reader.seek(oldPos)
        
        self.mtl = [FMeshMaterial_t() for _ in range(self.materialCount)]
        reader.readPtrObjects(self.mtl)
        
        self.collTree = reader.readU32()
        
        #self.texLayerIDArray = [FMeshTexLayerID_t() for _ in range(self.texLayerIDCount)]
        #reader.readPtrObjects(self.texLayerIDArray)
        self.texLayerIDArray = reader.readU32()
        
        reader.readPtrObject(self.meshIS)