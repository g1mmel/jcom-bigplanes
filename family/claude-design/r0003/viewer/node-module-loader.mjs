/** claude-design | Resolve the same pinned modules for non-browser QA. */
const modules={three:'./vendor/three.module.js','c130-controller':'./controller.mjs','c130-pose-driver':'./pose-driver.mjs','gltf-loader':'./vendor/GLTFLoader.js','orbit-controls':'./vendor/OrbitControls.js'};
export async function resolve(specifier,context,next){if(specifier in modules)return {url:new URL(modules[specifier],import.meta.url).href,shortCircuit:true};return next(specifier,context);}
