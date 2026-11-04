package kr.or.keris.statistics.admin;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;

/**
 * 관리자 화면(초안). 이 패키지·/WEB-INF/views/admin·/static/admin 만 지우면 관리자 화면이 통째로 제거된다.
 * 다른 소스(Config·PageController·layout JSP·app.css·common.js)를 참조하지 않는다.
 * 화면은 상대 경로로 정적 파일을 읽으므로 컨텍스트·리버스 프록시 경로 계산도 필요 없다.
 */
@Controller
public class AdminPageController {

    @RequestMapping("/admin")
    public String admin() {
        return "admin/admin";
    }
}
