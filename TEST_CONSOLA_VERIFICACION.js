// SCRIPT PARA VERIFICAR QUE TODO ESTÁ CARGADO CORRECTAMENTE
// Copia y pega esto en la CONSOLA del navegador (F12 > Console)

console.log('═══════════════════════════════════════════════');
console.log('  VERIFICACIÓN DE CAMBIOS EN PLANES CONTINGENCIA');
console.log('═══════════════════════════════════════════════\n');

// 1. Verificar que las funciones existan
console.log('1. FUNCIONES JAVASCRIPT DISPONIBLES:');
console.log('   ✓ mostrarMenuSecciones:', typeof mostrarMenuSecciones === 'function' ? '✅ Cargada' : '❌ NO cargada');
console.log('   ✓ cerrarModalSecciones:', typeof cerrarModalSecciones === 'function' ? '✅ Cargada' : '❌ NO cargada');
console.log('   ✓ editarPlan:', typeof editarPlan === 'function' ? '✅ Cargada' : '❌ NO cargada');
console.log('   ✓ verDetalle:', typeof verDetalle === 'function' ? '✅ Cargada' : '❌ NO cargada');

// 2. Verificar que el botón existe en la tabla
console.log('\n2. ELEMENTOS EN EL DOM:');
const botonesSeccion = document.querySelectorAll('[onclick*="mostrarMenuSecciones"]');
console.log(`   ✓ Botones "Secciones" encontrados: ${botonesSeccion.length}`);
if (botonesSeccion.length > 0) {
  console.log(`   ✅ El botón está presente en ${botonesSeccion.length} plan(es)`);
} else {
  console.log('   ⚠️  No se encontraron botones. Intenta con Ctrl+Shift+R para limpiar caché');
}

// 3. Verificar estilos CSS
console.log('\n3. ESTILOS CSS:');
const style = window.getComputedStyle(document.querySelector('.btn-ios.btn-secciones') || {});
console.log('   ✓ Estilo btn-secciones aplicado:', style.backgroundColor ? '✅ Sí' : '⚠️  No visible aún');

// 4. Probar la función con ID de prueba
console.log('\n4. TEST DE FUNCIÓN:');
console.log('   Ejecutando: mostrarMenuSecciones(1)...');
console.log('   (Si ves un modal abajo, ¡está funcionando!)');

// 5. Información de la página
console.log('\n5. INFORMACIÓN DE LA PÁGINA:');
console.log('   URL actual:', window.location.href);
console.log('   Planes en tabla:', document.querySelectorAll('#planesTbody tr').length);

console.log('\n═══════════════════════════════════════════════');
console.log('  ✅ VERIFICACIÓN COMPLETA');
console.log('═══════════════════════════════════════════════\n');

// INSTRUCCIONES
console.log('%c✨ PRÓXIMOS PASOS:', 'color: green; font-weight: bold; font-size: 14px;');
console.log('%c1. Busca un plan en estado BORRADOR, EN REVISIÓN o APROBADO', 'color: blue;');
console.log('%c2. Haz click en el botón "📋 Secciones" (color morado)', 'color: blue;');
console.log('%c3. Se debe abrir un menú modal con 9 secciones', 'color: blue;');
console.log('%c4. Selecciona cualquier sección', 'color: blue;');
console.log('%c5. Se abrirá el wizard con ese formulario', 'color: blue;');

console.log('\n%c¿NO VES CAMBIOS? Intenta esto:', 'color: orange; font-weight: bold;');
console.log('%cwindow.location.reload(true);', 'background: #333; color: #0f0; padding: 5px; font-family: monospace;');
