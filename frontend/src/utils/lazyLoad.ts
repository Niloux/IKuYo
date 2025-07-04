// IntersectionObserver 懒加载工具
export function createLazyObserver(
    el: Element,
    onEnter: () => void,
    options: IntersectionObserverInit = { rootMargin: '100px' }
): IntersectionObserver {
    const observer = new window.IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                onEnter()
                observer.disconnect()
            }
        })
    }, options)
    observer.observe(el)
    return observer
}
