<template>
  <router-view></router-view>
</template>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
  background-color: #f0f2f5;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', Arial, sans-serif;
}
/* 自定义滚动条 */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 4px; }
</style>