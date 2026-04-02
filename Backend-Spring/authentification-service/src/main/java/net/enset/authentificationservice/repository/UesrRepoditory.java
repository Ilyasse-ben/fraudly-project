package net.enset.authentificationservice.repository;

import net.enset.authentificationservice.entity.User;
import org.springframework.data.jpa.repository.support.JpaRepositoryImplementation;

public interface UesrRepoditory extends JpaRepositoryImplementation<User,Long> {
}
