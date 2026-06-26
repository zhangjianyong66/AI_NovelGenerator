<template>
  <div class="workbench-layout">
    <aside class="workbench-layout__rail workbench-layout__rail--left">
      <slot name="left" />
    </aside>
    <main class="workbench-layout__main">
      <slot />
    </main>
    <aside class="workbench-layout__rail workbench-layout__rail--right">
      <slot name="right" />
    </aside>
  </div>
</template>
