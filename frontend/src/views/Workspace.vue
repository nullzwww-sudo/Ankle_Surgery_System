<template>
  <div class="workspace">
    <el-row :gutter="20">
      
      <el-col :span="14">
        <el-card shadow="hover" class="box-card">
          <template #header>
            <div class="card-header">
              <span class="title">影像预处理 (双模式)</span>
              <el-upload action="#" :auto-upload="false" :show-file-list="false" :on-change="onFileChange">
                <el-button type="primary">上传 X 光片</el-button>
              </el-upload>
            </div>
          </template>

          <div class="mode-indicator" v-if="imageUrl">
            <el-alert v-if="cropMode === 'point'" title="模式一：Point ROI 定位" description="移动鼠标，红框即为真实的 512x512 范围。移至关节处点击鼠标左键完成截取（类似盖章）。" type="warning" show-icon :closable="false" />
            <el-alert v-if="cropMode === 'seg'" title="模式二：Seg ROI 自由框选" description="请按住鼠标左键拖拽，画出囊括整个小腿的分割区域。松开鼠标完成截取。" type="success" show-icon :closable="false" />
            <el-alert v-if="cropMode === 'done'" title="预处理完成" description="数据已就绪，请在右侧检查预览图并点击提交运算。" type="info" show-icon :closable="false" />
          </div>

          <div 
            class="image-container" 
            v-if="imageUrl"
            @mousedown="onMouseDown"
            @mousemove="onMouseMove"
            @mouseup="onMouseUp"
            @mouseleave="onMouseUp"
            @dragstart.prevent
            :style="{ cursor: cropMode === 'point' ? 'none' : (cropMode === 'seg' ? 'crosshair' : 'default') }"
          >
            <img ref="imageRef" :src="imageUrl" alt="Source" class="source-image" @load="onImageLoad" />
            
            <div 
              v-show="box.w > 0 && box.h > 0"
              class="selection-box"
              :class="{ 'fixed-box': cropMode === 'point' }"
              :style="{ left: box.x + 'px', top: box.y + 'px', width: box.w + 'px', height: box.h + 'px' }"
            ></div>
          </div>
          
          <div v-else class="empty-text">请上传影像</div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="hover" class="box-card">
          <template #header>
            <div class="card-header">
              <span class="title">数据中心 & AI 发动机</span>
              <el-button type="danger" @click="submitToAI" :loading="isComputing" :disabled="!pointData || !segData">
                🚀 开始全栈 AI 运算
              </el-button>
            </div>
          </template>

          <div class="preview-area">
            <el-divider content-position="left">① Point ROI (Fixed 512x512)</el-divider>
            <div v-if="pointPreview" class="preview-box">
              <img :src="pointPreview" class="preview-img" />
              <p class="data-text">真实像素坐标: [X: {{ pointData.x }}, Y: {{ pointData.y }}] | 尺寸: [512 x 512]</p>
            </div>
            
            <el-divider content-position="left">② Seg ROI (自由区域)</el-divider>
            <div v-if="segPreview" class="preview-box">
              <img :src="segPreview" class="preview-img" />
              <p class="data-text">真实像素坐标: [X: {{ segData.x }}, Y: {{ segData.y }}] | 尺寸: [{{ segData.w }} x {{ segData.h }}]</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="reportVisible" title="📄 智能手术规划报告单" width="60%" center>
      <div v-loading="isGeneratingText" element-loading-text="Gemini 大模型正在思考规划方案...">
        <div class="report-content" v-if="aiResult">
          <div class="report-top">
            <img :src="aiResult.vis_image" class="result-img" />
            <div class="params-box">
              <el-descriptions title="AI 测算参数" :column="1" border>
                <el-descriptions-item label="AOA 分期"><el-tag type="danger">{{ aiResult.stage }}</el-tag></el-descriptions-item>
                <el-descriptions-item label="TAS 角">{{ aiResult.tas }} °</el-descriptions-item>
                <el-descriptions-item label="TTS 角">{{ aiResult.tts }} °</el-descriptions-item>
                <el-descriptions-item label="TTD 距离">{{ aiResult.ttd }} mm</el-descriptions-item>
              </el-descriptions>
            </div>
          </div>
          
          <el-divider />
          
          <div class="llm-plan" v-if="llmPlan">
            <h3>🤖 Gemini 专家规划方案</h3>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="截骨位置">{{ llmPlan.osteotomy_position }}</el-descriptions-item>
              <el-descriptions-item label="截骨角度">{{ llmPlan.osteotomy_angle }}</el-descriptions-item>
              <el-descriptions-item label="撑开高度">{{ llmPlan.distraction_height }}</el-descriptions-item>
              <el-descriptions-item label="固定方式">{{ llmPlan.fixation_method }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="reportVisible = false">关闭</el-button>
          <el-button type="primary" @click="savePlan" :disabled="isGeneratingText">确认方案并存档</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import request from '../utils/request'

// =====================
// 状态与模式控制
// =====================
const imageUrl = ref(null)
const imageRef = ref(null)
const cropMode = ref('none') // 'point' | 'seg' | 'done'

// 缩放比例与框坐标 (屏幕逻辑坐标)
const scaleX = ref(1)
const scaleY = ref(1)
const box = ref({ x: 0, y: 0, w: 0, h: 0 })
const isDrawing = ref(false)
const startPos = ref({ x: 0, y: 0 })

// 导出的数据 (真实像素与 Base64)
const pointPreview = ref(null)
const pointData = ref(null)
const segPreview = ref(null)
const segData = ref(null)

// 结果状态
const isComputing = ref(false)
const reportVisible = ref(false)
const isGeneratingText = ref(false)
const aiResult = ref(null)
const llmPlan = ref(null)

// =====================
// 画板核心逻辑
// =====================
const onFileChange = (file) => {
  imageUrl.value = URL.createObjectURL(file.raw)
  cropMode.value = 'point' // 图片上传后，立刻进入固定尺寸定位模式
  pointData.value = null
  segData.value = null
  box.value = { x: -999, y: -999, w: 0, h: 0 }
}

const onImageLoad = () => {
  const img = imageRef.value
  scaleX.value = img.naturalWidth / img.width
  scaleY.value = img.naturalHeight / img.height
}

const onMouseMove = (e) => {
  const img = imageRef.value
  if (!img) return
  const rect = img.getBoundingClientRect()
  const mouseX = e.clientX - rect.left
  const mouseY = e.clientY - rect.top

  if (cropMode.value === 'point') {
    // 【模式一】512x512 寻像器模式：框跟随鼠标，尺寸固定
    const displayW = 512 / scaleX.value
    const displayH = 512 / scaleY.value
    // 让鼠标位于框中心，同时防止超出边界
    let cx = mouseX - displayW / 2
    let cy = mouseY - displayH / 2
    cx = Math.max(0, Math.min(cx, img.width - displayW))
    cy = Math.max(0, Math.min(cy, img.height - displayH))
    
    box.value = { x: cx, y: cy, w: displayW, h: displayH }
  } 
  else if (cropMode.value === 'seg' && isDrawing.value) {
    // 【模式二】自由框选模式：拖拽更新框尺寸
    let currentX = Math.max(0, Math.min(mouseX, img.width))
    let currentY = Math.max(0, Math.min(mouseY, img.height))
    box.value.x = Math.min(startPos.value.x, currentX)
    box.value.y = Math.min(startPos.value.y, currentY)
    box.value.w = Math.abs(currentX - startPos.value.x)
    box.value.h = Math.abs(currentY - startPos.value.y)
  }
}

const onMouseDown = (e) => {
  if (cropMode.value === 'point') {
    // 点击即盖章，直接截取 Point ROI
    performCrop('point')
    cropMode.value = 'seg' // 自动切入第二阶段
    box.value = { x: 0, y: 0, w: 0, h: 0 } // 清空视窗框
    ElMessage.success('Point ROI 定位成功！现在请拖拽画出完整的腿部区域。')
  } 
  else if (cropMode.value === 'seg') {
    // 自由模式按下，记录起点
    isDrawing.value = true
    const rect = imageRef.value.getBoundingClientRect()
    startPos.value = { x: e.clientX - rect.left, y: e.clientY - rect.top }
    box.value = { x: startPos.value.x, y: startPos.value.y, w: 0, h: 0 }
  }
}

const onMouseUp = () => {
  if (cropMode.value === 'seg' && isDrawing.value) {
    isDrawing.value = false
    if (box.value.w > 10 && box.value.h > 10) {
      performCrop('seg')
      cropMode.value = 'done'
      box.value = { x: -999, y: -999, w: 0, h: 0 } // 隐藏框
    }
  }
}

const performCrop = (type) => {
  const img = imageRef.value
  const realX = Math.round(box.value.x * scaleX.value)
  const realY = Math.round(box.value.y * scaleY.value)
  const realW = type === 'point' ? 512 : Math.round(box.value.w * scaleX.value)
  const realH = type === 'point' ? 512 : Math.round(box.value.h * scaleY.value)

  const canvas = document.createElement('canvas')
  canvas.width = realW
  canvas.height = realH
  const ctx = canvas.getContext('2d')
  ctx.drawImage(img, realX, realY, realW, realH, 0, 0, realW, realH)

  const resultData = { x: realX, y: realY, w: realW, h: realH }
  const base64 = canvas.toDataURL(type === 'point' ? 'image/jpeg' : 'image/png')

  if (type === 'point') {
    pointPreview.value = base64
    pointData.value = resultData
  } else {
    segPreview.value = base64
    segData.value = resultData
  }
}

// =====================
// 真实 API 通信链路 (三连击)
// =====================
// 工具：Base64 转 Blob
const dataURLtoBlob = (dataurl) => {
  let arr = dataurl.split(','), mime = arr[0].match(/:(.*?);/)[1]
  let bstr = atob(arr[1]), n = bstr.length, u8arr = new Uint8Array(n)
  while(n--){ u8arr[n] = bstr.charCodeAt(n) }
  return new Blob([u8arr], {type: mime})
}

const submitToAI = async () => {
  isComputing.value = true
  aiResult.value = null
  llmPlan.value = null
  
  try {
    const pointBlob = dataURLtoBlob(pointPreview.value)
    const segBlob = dataURLtoBlob(segPreview.value)

    // 接口 1: 获取 AOA 分期
    ElMessage.info('步骤 1/3：正在进行 AOA 分期判定...')
    const fd1 = new FormData()
    fd1.append('point_image', pointBlob, 'point.jpg')
    const resAoa = await request.post('/api/ai/aoa_stage', fd1)
    const stage = resAoa.stage

    // 接口 2: 关键点映射与角度计算
    ElMessage.info('步骤 2/3：正在进行关键点推演与测算...')
    const fd2 = new FormData()
    fd2.append('point_image', pointBlob, 'point.jpg')
    fd2.append('seg_image', segBlob, 'seg.png')
    fd2.append('point_json_content', JSON.stringify(pointData.value))
    fd2.append('seg_json_content', JSON.stringify(segData.value))
    const resCalc = await request.post('/api/ai/calculate_plan', fd2)
    
    // 聚合数据准备展示
    aiResult.value = {
      stage: stage,
      tas: resCalc.tas,
      tts: resCalc.tts,
      ttd: resCalc.ttd_ap_mm,
      vis_image: resCalc.vis_image_base64
    }
    
    // 弹窗展示阶段成果
    reportVisible.value = true
    isGeneratingText.value = true
    
    // 接口 3: 调用大模型生成手术规划
    ElMessage.info('步骤 3/3：Gemini 专家正在编写手术方案...')
    const fd3 = new FormData()
    fd3.append('stage', stage)
    fd3.append('tas', resCalc.tas)
    fd3.append('tts', resCalc.tts)
    fd3.append('ttd', resCalc.ttd_ap_mm)
    fd3.append('age', 45)       // 实际应从上方患者信息带入
    fd3.append('gender', '男')
    
    const resPlan = await request.post('/api/ai/generate_plan', fd3)
    llmPlan.value = resPlan

    ElMessage.success('AI 运算全部完成！')
  } catch (error) {
    console.error(error)
  } finally {
    isComputing.value = false
    isGeneratingText.value = false
  }
}

const savePlan = () => {
  ElMessage.success('手术方案已归档至数据库！')
  reportVisible.value = false
}
</script>

<style scoped>
.workspace { margin-top: 10px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.title { font-weight: bold; font-size: 16px; }
.mode-indicator { margin-bottom: 15px; }

/* 原生画板核心样式 */
.image-container { position: relative; display: inline-block; border-radius: 8px; overflow: hidden; user-select: none; background: #000; text-align: center; width: 100%; min-height: 400px;}
.source-image { display: block; max-width: 100%; max-height: 600px; margin: 0 auto; pointer-events: none; }

/* 红框样式 */
.selection-box { position: absolute; border: 2px dashed #ff4949; background-color: rgba(255, 73, 73, 0.15); pointer-events: none; }
.fixed-box { border: 2px solid #ff4949; background-color: rgba(255, 73, 73, 0.3); box-shadow: 0 0 10px rgba(255,0,0,0.5); }

.empty-text { height: 400px; display: flex; justify-content: center; align-items: center; color: #909399; background-color: #fafafa; border: 1px dashed #dcdfe6; border-radius: 8px; }

/* 预览区样式 */
.preview-area { padding: 10px; }
.preview-box { text-align: center; margin-bottom: 20px; background: #f8f9fa; padding: 15px; border-radius: 8px;}
.preview-img { max-width: 100%; max-height: 180px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.data-text { font-size: 12px; color: #606266; margin-top: 10px; font-family: monospace; }

/* 报告单弹窗样式 */
.report-top { display: flex; gap: 20px; align-items: center; }
.result-img { max-width: 300px; border-radius: 8px; border: 1px solid #ebeef5; }
.params-box { flex: 1; }
.llm-plan h3 { margin-top: 0; color: #303133; }
</style>