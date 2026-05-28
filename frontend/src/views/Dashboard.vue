<template>
  <el-container class="layout-container">
    <el-aside width="220px" class="aside">
      <div class="logo"><span>🦴 AI 骨科工作站</span></div>
      <el-menu router default-active="/dashboard/workspace" background-color="#001529" text-color="#a6adb4" active-text-color="#ffffff">
        <el-menu-item index="/dashboard/workspace">
          <span>🎯 AI 术前规划工作台</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">踝上截骨矫形手术规划系统 (医师端)</div>
        <el-button type="danger" plain size="small" @click="$router.push('/')">退出登录</el-button>
      </el-header>
      <el-main class="main-content">
         <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout-container { height: 100vh; }
.aside { background-color: #001529; display: flex; flex-direction: column; }
.logo { height: 60px; line-height: 60px; text-align: center; color: #fff; font-size: 18px; font-weight: bold; background-color: #002140; }
.el-menu { border-right: none; }
.header { background-color: #fff; line-height: 60px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 4px rgba(0,21,41,.08); z-index: 10; }
.main-content { background-color: #f0f2f5; padding: 20px; }
</style>